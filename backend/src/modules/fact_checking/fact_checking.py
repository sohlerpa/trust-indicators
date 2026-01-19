from datetime import datetime, timezone
import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Any, Dict, Tuple

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

FACTCHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

FACTCHECK_DEBUG = os.getenv("FACTCHECK_DEBUG", "").lower() in ("1", "true", "yes", "on")


def _dbg(msg: str, *, claim_id: str | None = None):
    if not FACTCHECK_DEBUG:
        return
    prefix = f"[factcheck]{'[' + claim_id + ']' if claim_id else ''}"
    print(f"{prefix} {msg}")


# =========================
# Data Models
# =========================

@dataclass
class FactCheckTrustStats:
    extractedClaims: int
    checkedClaims: int
    droppedClaims: int
    dropReasons: dict  # e.g. {"noEvidence": 3, "keywordExtractionFailed": 1, "assertionFailed": 0}


@dataclass
class FactCheckTrustClaimDTO:
    id: str
    claimText: str
    sourceText: str
    startChar: int
    endChar: int
    reason: Optional[str]
    query: dict  # {"primary": str, "alternatives": List[str]}
    verdict: str  # "true" | "false" | "unclear"
    confidence: float
    summary: str
    reasoning: str
    sources: List[dict]  # list of SourceRef dicts


@dataclass
class FactCheckTrustDTO:
    articleId: str
    generatedAt: str  # ISO
    stats: FactCheckTrustStats
    claims: List[FactCheckTrustClaimDTO]


@dataclass
class ClaimSpan:
    claim_text: str  # normalized factual claim
    start_char: int  # start index in plain text
    end_char: int  # end index in plain text
    source_text: str  # exact text slice from article
    reason: Optional[str] = None  # why this is checkable (optional)


@dataclass
class ExtractedClaims:
    plain_text: str  # HTML stripped to text (for indexing)
    claims: List[ClaimSpan]


@dataclass
class FactCheckReview:
    publisher: Optional[str]
    publisher_site: Optional[str]
    title: Optional[str]
    url: Optional[str]
    textual_rating: Optional[str]
    review_date: Optional[str]
    language_code: Optional[str]


@dataclass
class FactCheckClaim:
    text: Optional[str]
    claimant: Optional[str]
    claim_date: Optional[str]
    reviews: List[FactCheckReview]


class Verdict(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNCLEAR = "unclear"


@dataclass
class SourceRef:
    publisher: Optional[str]
    publisher_site: Optional[str]
    title: Optional[str]
    url: Optional[str]
    review_date: Optional[str]
    textual_rating: Optional[str]
    language_code: Optional[str]


@dataclass
class FactAssertionResult:
    input_claim: str
    verdict: Verdict
    confidence: float  # 0.0..1.0
    summary: str
    reasoning: str
    sources: List[SourceRef]
    notes: Optional[str] = None


@dataclass
class FactCheckQuery:
    primary: str
    alternatives: List[str]


@dataclass
class CheckedClaim:
    claim_id: str
    span: ClaimSpan
    query: FactCheckQuery
    fact_checks: List[FactCheckClaim]
    assertion: FactAssertionResult


# =========================
# Utilities
# =========================

def _claim_id(article_id: str, start: int, end: int, claim_text: str) -> str:
    raw = f"{article_id}:{start}:{end}:{claim_text}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _to_claim_dto(article_id: str, checked: CheckedClaim) -> FactCheckTrustClaimDTO:
    return FactCheckTrustClaimDTO(
        id=_claim_id(article_id, checked.span.start_char, checked.span.end_char, checked.span.claim_text),
        claimText=checked.span.claim_text,
        sourceText=checked.span.source_text,
        startChar=checked.span.start_char,
        endChar=checked.span.end_char,
        reason=checked.span.reason,
        query={"primary": checked.query.primary, "alternatives": checked.query.alternatives},
        verdict=str(
            checked.assertion.verdict.value
            if hasattr(checked.assertion.verdict, "value")
            else checked.assertion.verdict
        ),
        confidence=float(checked.assertion.confidence),
        summary=checked.assertion.summary,
        reasoning=checked.assertion.reasoning,
        sources=[asdict(s) for s in checked.assertion.sources],
    )


def post_with_retry(
        client: httpx.Client,
        url: str,
        *,
        headers: dict,
        json_body: dict,
        retries: int = 3,
        base_delay: float = 1.0,
):
    for attempt in range(retries):
        if attempt != 0:
            print(f"Retrying: Attempt {attempt + 1}/{retries}")
        try:
            resp = client.post(url, headers=headers, json=json_body)
            resp.raise_for_status()
            return resp
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt < retries - 1:
                sleep = base_delay * (2 ** attempt) + random.uniform(0, 0.3)
                time.sleep(sleep)
                continue
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500 and attempt < retries - 1:
                sleep = base_delay * (2 ** attempt) + random.uniform(0, 0.3)
                time.sleep(sleep)
                continue
            raise


def html_to_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "img"]):
        tag.decompose()
    text = soup.get_text()
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


# =========================
# Evidence packing + stable IDs (Option C)
# =========================

def extract_claims_from_html(
        html: str,
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash-lite",
) -> ExtractedClaims:
    import json
    import httpx

    plain_text = html_to_plain_text(html)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_instruction = (
        "You prepare claims to be checked with the Google Fact Check Tools API (claims:search).\n\n"
        "Goal: extract ONLY claims that are (1) ATOMIC and (2) likely to have existing third-party fact-check coverage.\n\n"
        "A claim is ACCEPTABLE only if it is a standalone factual assertion that could be searched verbatim and judged true/false.\n"
        "Prefer claims with absolute language and clear predicates (often already fact-checked):\n"
        "- \"X is the only...\"\n"
        "- \"No vaccines were...\"\n"
        "- \"Never safety tested\"\n"
        "- \"CDC study found <1%\" (named study)\n"
        "- named lawsuit/whistleblower + specific allegation\n"
        "- concrete numeric prevalence statements tied to a study/place/time\n\n"
        "STRONGLY PREFER extracting claims in the form they appear (keep meaning), but you MAY do minimal normalization\n"
        "ONLY to make the claim self-contained (e.g., expand pronouns like \"that study\" -> \"the 2010 Lazarus study\" if present in text).\n\n"
        "DROP (do not extract) items that are hard for automated fact-check search:\n"
        "- conversational filler (\"I think\", \"as of this morning\") unless the claim is still a clean numeric assertion\n"
        "- broad multi-part paragraphs that bundle multiple claims\n"
        "- purely local counts or routine epidemiology stats UNLESS phrased as a prominent comparative record (\"second biggest since 2000\")\n"
        "- vague causal speculation (\"we know it's a toxin\") unless it names a specific authority + year + conclusion\n\n"
        "Atomicity rules:\n"
        "- EXACTLY ONE checkable assertion per claim.\n"
        "- The context should still be clear, so the fact can be checked at its own without the article.\n"
        "- If a sentence contains multiple assertions, split them.\n"
        "- Avoid embedding extra justifications.\n\n"
        "Searchability rules (critical):\n"
        "- Choose claims that can be searched with short keyword queries (names, agencies, study titles, years, 'placebo', 'exempt', 'Lazarus').\n"
        "- Prefer claims that include at least one of: a named institution (CDC/FDA/NIH/EPA/Merck), a named study, a year, or a strong universal quantifier.\n\n"
        "Output constraints:\n"
        "- Output JSON only.\n"
        "- Provide exact character offsets into the PROVIDED plain text.\n"
        "- Offsets must match exactly.\n"
        "- Return at most 10 claims (pick highest-value + most searchable).\n"
    )

    response_schema = {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_text": {"type": "string"},
                        "start_char": {"type": "integer"},
                        "end_char": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["claim_text", "start_char", "end_char"],
                },
            }
        },
        "required": ["claims"],
    }

    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": json.dumps(
                            {
                                "text": plain_text,
                                "task": (
                                    "Extract up to 10 ATOMIC, searchable factual claims that a fact-check database is likely to contain.\n"
                                    "Each claim must be a single self-contained assertion (one predicate).\n"
                                    "Prefer absolute/record/never/only/exempt/placebo-tested/CDC-study-found patterns.\n"
                                    "Return claim_text as ONE full sentence.\n"
                                    "Return start_char/end_char offsets referring to THIS exact text.\n"
                                    "If a statement is not suitable for automated fact-check search, do NOT extract it."
                                )
                            },
                            ensure_ascii=False,
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key,
    }

    with httpx.Client(timeout=35) as client:
        resp = post_with_retry(
            client,
            url,
            headers=headers,
            json_body=body,
            retries=3,
        )
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)

    claims: List[ClaimSpan] = []
    for c in parsed["claims"]:
        start = c["start_char"]
        end = c["end_char"]
        claims.append(
            ClaimSpan(
                claim_text=c["claim_text"],
                start_char=start,
                end_char=end,
                source_text=plain_text[start:end],
                reason=c.get("reason"),
            )
        )
    extracted_claims = ExtractedClaims(
        plain_text=plain_text,
        claims=claims,
    )
    print("Found claims: ", {len(extracted_claims.claims)})
    for claim in extracted_claims.claims:
        print(claim.claim_text, "\n")

    return extracted_claims


def search_for_claim_multi(
        query: FactCheckQuery,
        *,
        api_key: str,
        max_searches: int = 5,
) -> Tuple[List[FactCheckClaim], List[str]]:
    """
    Runs up to max_searches searches (primary + alternatives),
    merges results, de-dupes, and returns:
      (merged_claims, used_queries)
    """
    # Build ordered unique list of query strings
    all_q = [query.primary] + list(query.alternatives or [])
    seen = set()
    queries: List[str] = []
    for q in all_q:
        q = (q or "").strip()
        if not q or q in seen:
            continue
        seen.add(q)
        queries.append(q)

    used_queries: List[str] = []
    merged: List[FactCheckClaim] = []
    dedup_keys: set[str] = set()

    def _key(fc: FactCheckClaim) -> str:
        # Prefer stable-ish de-dupe key: claim text + claimant + first review url
        first_url = None
        if fc.reviews:
            for r in fc.reviews:
                if r.url:
                    first_url = r.url
                    break
        return f"{(fc.text or '').strip()}|{(fc.claimant or '').strip()}|{(first_url or '').strip()}"

    for q in queries[:max_searches]:
        results = search_for_keywords(q, api_key)
        used_queries.append(q)

        for fc in results:
            k = _key(fc)
            if k in dedup_keys:
                continue
            dedup_keys.add(k)
            merged.append(fc)

    return merged, used_queries


def _canonical_source_id(*, url: Optional[str], title: Optional[str], publisher: Optional[str]) -> str:
    """
    Stable ID based on the review entry itself.
    Prefer URL (best), otherwise title+publisher.
    """
    key = (url or "").strip()
    if not key:
        key = f"{(publisher or '').strip()}|{(title or '').strip()}"
    if not key:
        key = "unknown"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def _facts_to_llm_evidence(
        fact_check_claims: List[FactCheckClaim],
) -> Tuple[List[dict[str, Any]], Dict[str, SourceRef]]:
    """
    Returns:
      - evidence payload for the LLM, where EACH review includes a review_id
      - id -> SourceRef mapping for exact reconstruction later
    """
    evidence: List[dict[str, Any]] = []
    id_to_source: Dict[str, SourceRef] = {}

    for c in fact_check_claims:
        packed_reviews: List[dict[str, Any]] = []
        for r in c.reviews:
            rid = _canonical_source_id(url=r.url, title=r.title, publisher=r.publisher)

            # First writer wins if collision; collisions are unlikely when url exists.
            if rid not in id_to_source:
                id_to_source[rid] = SourceRef(
                    publisher=r.publisher,
                    publisher_site=r.publisher_site,
                    title=r.title,
                    url=r.url,
                    review_date=r.review_date,
                    textual_rating=r.textual_rating,
                    language_code=r.language_code,
                )

            packed_reviews.append(
                {
                    "review_id": rid,
                    "publisher": r.publisher,
                    "publisher_site": r.publisher_site,
                    "title": r.title,
                    "url": r.url,
                    "textual_rating": r.textual_rating,
                    "review_date": r.review_date,
                    "language_code": r.language_code,
                }
            )

        evidence.append(
            {
                "claim_text": c.text,
                "claimant": c.claimant,
                "claim_date": c.claim_date,
                "reviews": packed_reviews,
            }
        )

    return evidence, id_to_source


# =========================
# Gemini: keywords + assertion
# =========================

def extract_keywords_from_claim(
        claim: str,
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash-lite",
) -> FactCheckQuery:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_instruction = (
        "You generate search queries for the Google Fact Check Tools API (claims:search).\n"
        "Goal: HIGH RECALL. Prefer broad topic queries that are likely to match existing fact-check entries.\n"
        "The index often does NOT match exact claim wording, numbers, or specific time phrases.\n\n"
        "Output JSON only:\n"
        "- primary: best high-recall query\n"
        "- alternatives: 2 to 4 additional queries (TOTAL 3 to 5 searches)\n\n"
        "Query style rules (important):\n"
        "- Keep queries SHORT: 2–4 words preferred (max 6).\n"
        "- Use mostly NOUNS. Avoid verbs and adjectives.\n"
        "- Avoid time/rank phrases like: 'since 2000', 'second biggest', 'largest', exact counts.\n"
        "- Avoid abstract/meta words: 'comparison', 'historical', 'scale', 'evidence', 'claims', 'requirements'.\n"
        "- Primary must be anchored: it MUST include a specific anchor from the claim text (e.g., MMR/measles/mumps/VAERS/Lazarus/Merck/CDC/FDA/COVID).\n"
        "- Alternatives may include at most ONE broad backoff query, but the others must still include an anchor from the claim.\n"
        "- Never output ultra-broad single-word queries like: 'outbreak', 'testing', 'safety', 'vaccines'.\n"
        "How to choose terms:\n"
        "- Prefer anchors if present: Merck, MMR, VAERS, Lazarus, CDC, FDA, Gardasil, COVID.\n"
        "- Otherwise use the main domain nouns: vaccine safety, placebo trial, vaccine testing, VAERS reporting,\n"
        "  mumps vaccine, measles outbreak, autism prevalence.\n\n"
        "Distinctness requirement:\n"
        "- Do NOT output word-order permutations.\n"
        "- Each alternative must be a different retrieval angle (different anchor/topic combo).\n\n"
        "Return keywords only (no full sentences).\n"
        "Fallback rule: if unsure, output a broader 2–3 word topic query instead of adding specificity."
    )

    response_schema = {
        "type": "object",
        "properties": {
            "primary": {"type": "string"},
            "alternatives": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["primary", "alternatives"],
    }

    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": json.dumps(
                            {
                                "claim": claim,
                                "task": (
                                    "Return 3–5 SHORT high-recall keyword queries (2–4 words preferred) to find matching fact-check entries.\n"
                                    "Be broader/open rather than specific. Avoid years, rankings, and abstract/meta wording.\n"
                                    "Return JSON: primary + alternatives."
                                )
                            },
                            ensure_ascii=False,
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema,
        },
    }

    headers = {"Content-Type": "application/json", "x-goog-api-key": gemini_api_key}

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse keyword extraction result: {data}") from e

    return FactCheckQuery(
        primary=parsed["primary"].strip(),
        alternatives=[a.strip() for a in parsed["alternatives"]],
    )


def search_for_keywords(keywords: str, api_key: str) -> List[FactCheckClaim]:
    time.sleep(0.8)  # REQUIRED

    with httpx.Client(timeout=10) as client:
        params = {"query": keywords, "pageSize": 30, "key": api_key}
        resp = client.get(FACTCHECK_ENDPOINT, params=params)

        if resp.status_code == 403:
            raise RuntimeError("FactCheck API rate-limited")

        resp.raise_for_status()
        data = resp.json()

    raw_claims = data.get("claims", [])
    claims: List[FactCheckClaim] = []

    for c in raw_claims:
        reviews: List[FactCheckReview] = []
        for r in c.get("claimReview", []):
            reviews.append(
                FactCheckReview(
                    publisher=(r.get("publisher") or {}).get("name"),
                    publisher_site=(r.get("publisher") or {}).get("site"),
                    title=r.get("title"),
                    url=r.get("url"),
                    textual_rating=r.get("textualRating"),
                    review_date=r.get("reviewDate"),
                    language_code=r.get("languageCode"),
                )
            )
        claims.append(
            FactCheckClaim(
                text=c.get("text"),
                claimant=c.get("claimant"),
                claim_date=c.get("claimDate"),
                reviews=reviews,
            )
        )

    print(f"found {len(claims)} claims for {keywords}")
    return claims


def assert_claims_to_facts_batch(
        items: List[CheckedClaim],
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash-lite",
        timeout_s: int = 100,
) -> Dict[str, FactAssertionResult]:
    """
    Returns dict: claim_id -> FactAssertionResult
    (No more brittle list-index coupling.)
    """
    if not items:
        return {}

    # Build per-claim evidence payloads + per-claim id->SourceRef maps
    evidence_payloads: Dict[str, List[dict[str, Any]]] = {}
    id_maps: Dict[str, Dict[str, SourceRef]] = {}

    for it in items:
        ev, id_map = _facts_to_llm_evidence(it.fact_checks)
        evidence_payloads[it.claim_id] = ev
        id_maps[it.claim_id] = id_map

    response_schema = {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_id": {"type": "string"},
                        "verdict": {"type": "string", "enum": ["true", "false", "unclear"]},
                        "confidence": {"type": "number"},
                        "summary": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "used_source_ids": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": "string"},
                    },
                    "required": [
                        "claim_id",
                        "verdict",
                        "confidence",
                        "summary",
                        "reasoning",
                        "used_source_ids",
                        "notes",
                    ],
                },
            }
        },
        "required": ["results"],
    }

    system_instruction = (
        "You are a fact-checking assistant.\n"
        "You must ONLY use the provided evidence for EACH claim.\n"
        "Do NOT use external knowledge.\n"
        "Do NOT invent sources.\n\n"
        "VERY IMPORTANT SELECTION RULE:\n"
        "- If evidence is non-empty for a claim, you MUST select at least ONE review_id in used_source_ids.\n"
        "- Even if the verdict is 'unclear', pick the SINGLE closest matching review_id.\n"
        "- Only return used_source_ids = [] when the evidence list is empty.\n\n"
        "Return results with the SAME claim_id you received.\n"
    )

    user_prompt = {
        "task": (
            "For each item, decide true/false/unclear using ONLY its evidence.\n"
            "Return JSON matching the schema.\n"
            "Important:\n"
            "- If evidence is about a different claim or not close, choose 'unclear' (low confidence).\n"
            "- STILL you MUST include >=1 used_source_id whenever evidence is non-empty.\n"
            "- Put ONLY review_id values you relied on into used_source_ids.\n"
            "- Keep summary 1-2 sentences. Keep reasoning concise but specific.\n"
        ),
        "items": [
            {
                "claim_id": it.claim_id,
                "input_claim": it.span.claim_text,
                "evidence": evidence_payloads[it.claim_id],
            }
            for it in items
        ],
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(user_prompt, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema,
        },
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": gemini_api_key}

    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(f"{resp.status_code}: {resp.text}")
        data = resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        raw_results = parsed["results"]
    except Exception as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {data}") from e

    # Parse into claim_id -> FactAssertionResult, with strict source-id filtering + fallback
    out: Dict[str, FactAssertionResult] = {}
    seen_ids: set[str] = set()

    for r in raw_results:
        claim_id = str(r["claim_id"]).strip()
        seen_ids.add(claim_id)

        verdict = Verdict(r["verdict"])
        confidence = float(r["confidence"])
        summary = str(r["summary"])
        reasoning = str(r["reasoning"])
        notes = r.get("notes")

        used_ids = [str(x).strip() for x in (r.get("used_source_ids") or []) if str(x).strip()]
        id_map = id_maps.get(claim_id, {})

        _dbg(f"assert verdict={verdict} conf={confidence:.2f} used_ids={len(used_ids)} id_map={len(id_map)}", claim_id=claim_id)

        # Filter to valid review_ids
        sources: List[SourceRef] = []
        dropped = 0
        for rid in used_ids:
            src = id_map.get(rid)
            if not src:
                dropped += 1
                continue
            sources.append(src)

        if dropped:
            notes = (notes or "") + f" | dropped_unknown_source_ids={dropped}"

        # Fallback: if model returned no valid sources but evidence exists, pick 1 best-effort source
        # (This prevents "0 checked, everything dropped" while still surfacing uncertainty.)
        if not sources and id_map:
            fallback_rid = next(iter(id_map.keys()))
            sources = [id_map[fallback_rid]]
            notes = (notes or "") + " | fallback_source_selected"
            verdict = Verdict.UNCLEAR if verdict != Verdict.FALSE and verdict != Verdict.TRUE else verdict
            confidence = min(confidence, 0.35)  # keep it clearly low if we had to fallback
            _dbg(f"fallback picked review_id={fallback_rid}", claim_id=claim_id)

        out[claim_id] = FactAssertionResult(
            input_claim="",  # filled in below from original item (safer than trusting model)
            verdict=verdict,
            confidence=confidence,
            summary=summary,
            reasoning=reasoning,
            sources=sources,
            notes=notes,
        )

    # Ensure every input claim has an output entry (even if missing from model output)
    for it in items:
        if it.claim_id not in out:
            _dbg("missing model result -> create placeholder", claim_id=it.claim_id)
            out[it.claim_id] = FactAssertionResult(
                input_claim=it.span.claim_text,
                verdict=Verdict.UNCLEAR,
                confidence=0.0,
                summary="No result returned for this claim.",
                reasoning="The batch model output did not include an entry for this claim_id.",
                sources=[],
                notes="missing_batch_result",
            )
        else:
            # Fill input_claim from our canonical item text (prevents mismatches / hallucinated text)
            out[it.claim_id].input_claim = it.span.claim_text

    # Debug: model returned unknown IDs
    if FACTCHECK_DEBUG:
        unknown = [cid for cid in seen_ids if cid not in {it.claim_id for it in items}]
        if unknown:
            _dbg(f"model returned {len(unknown)} unknown claim_id(s): {unknown[:3]}…")

    return out


# =========================
# Top-level function (PATCH THE CANDIDATES + ATTACHMENT PARTS)
# =========================

def check_facts_for_html(content_html: str, *, article_id: str) -> FactCheckTrustDTO:
    api_key = os.environ["GEMINI_API_KEY"]
    fact_api_key = os.environ["FACT_CHECKING_API_KEY"]

    extracted = extract_claims_from_html(content_html, gemini_api_key=api_key)

    extracted_count = len(extracted.claims)

    dropped_no_evidence = 0
    dropped_keyword_failed = 0
    dropped_assertion_failed = 0

    # NEW: richer counters for debugging / telemetry
    dropped_missing_batch_result = 0
    checked_with_no_sources = 0

    candidates: List[CheckedClaim] = []

    for span in extracted.claims:
        claim_id = _claim_id(article_id, span.start_char, span.end_char, span.claim_text)

        try:
            query = extract_keywords_from_claim(span.claim_text, gemini_api_key=api_key)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
            dropped_keyword_failed += 1
            _dbg(f"drop keywordExtractionFailed: {type(e).__name__}", claim_id=claim_id)
            continue

        fact_checks, used_queries = search_for_claim_multi(query, api_key=fact_api_key, max_searches=5)
        _dbg(f"searched={used_queries}", claim_id=claim_id)

        if not fact_checks:
            dropped_no_evidence += 1
            _dbg("drop noEvidence: fact-check api returned 0 claims", claim_id=claim_id)
            continue

        candidates.append(
            CheckedClaim(
                claim_id=claim_id,
                span=span,
                query=query,
                fact_checks=fact_checks,
                assertion=FactAssertionResult(
                    input_claim=span.claim_text,
                    verdict=Verdict.UNCLEAR,
                    confidence=0.0,
                    summary="pending",
                    reasoning="pending",
                    sources=[],
                    notes="pending",
                ),
            )
        )

    assertions_by_id: Dict[str, FactAssertionResult] = {}
    try:
        _dbg(f"candidates_for_assertion={len(candidates)}")
        assertions_by_id = assert_claims_to_facts_batch(candidates, gemini_api_key=api_key)
    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError, RuntimeError) as e:
        dropped_assertion_failed += len(candidates)
        _dbg(f"assertion batch failed: {type(e).__name__}: {e}")
        candidates = []
        assertions_by_id = {}

    checked: List[CheckedClaim] = []
    for c in candidates:
        a = assertions_by_id.get(c.claim_id)
        if not a:
            dropped_assertion_failed += 1
            dropped_missing_batch_result += 1
            _dbg("drop assertionFailed: missing result for claim_id", claim_id=c.claim_id)
            continue

        # skip placeholders entirely
        if a.notes and "missing_batch_result" in a.notes:
            dropped_assertion_failed += 1
            dropped_missing_batch_result += 1
            _dbg("drop assertionFailed: missing_batch_result placeholder", claim_id=c.claim_id)
            continue

        # skip "fallback-only" results (broad evidence, no close match)
        if a.notes and "fallback_source_selected" in a.notes:
            dropped_no_evidence += 1
            _dbg("drop noEvidence: fallback_source_selected (no close match)", claim_id=c.claim_id)
            continue

        # keep but annotate if no sources (optional)
        if not a.sources:
            checked_with_no_sources += 1
            a.notes = (a.notes or "") + " | no_sources_selected"
            _dbg("kept but no sources selected", claim_id=c.claim_id)

        c.assertion = a
        checked.append(c)

    checked_count = len(checked)
    dropped_count = extracted_count - checked_count

    return FactCheckTrustDTO(
        articleId=article_id,
        generatedAt=datetime.now(timezone.utc).isoformat(),
        stats=FactCheckTrustStats(
            extractedClaims=extracted_count,
            checkedClaims=checked_count,
            droppedClaims=dropped_count,
            dropReasons={
                "noEvidence": dropped_no_evidence,
                "keywordExtractionFailed": dropped_keyword_failed,
                "assertionFailed": dropped_assertion_failed,
                # NEW: debugging breakdown
                "missingBatchResult": dropped_missing_batch_result,
                "checkedButNoSources": checked_with_no_sources,
            },
        ),
        claims=[_to_claim_dto(article_id, c) for c in checked],
    )