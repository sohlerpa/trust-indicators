from datetime import datetime, timezone
import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

FACTCHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


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
    confidence: float  # 0.0..1.0 (how strongly supported by the *provided* evidence)
    summary: str  # 1-2 sentences
    reasoning: str  # short explanation, must reference evidence fields
    sources: List[SourceRef]  # ONLY from fact_check_claims reviews
    notes: Optional[str] = None  # e.g. "no matching fact-checks found"


@dataclass
class FactCheckQuery:
    primary: str
    alternatives: List[str]


@dataclass
class CheckedClaim:
    span: ClaimSpan
    query: FactCheckQuery
    fact_checks: List[FactCheckClaim]
    assertion: FactAssertionResult



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
        verdict=str(checked.assertion.verdict.value if hasattr(checked.assertion.verdict, "value") else checked.assertion.verdict),
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
        try:
            resp = client.post(url, headers=headers, json=json_body)
            resp.raise_for_status()
            return resp

        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
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

    # Remove non-textual elements you don’t want claims from
    for tag in soup(["script", "style", "img"]):
        tag.decompose()

    text = soup.get_text()
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def extract_claims_from_html(
        html: str,
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash",
) -> ExtractedClaims:
    import json
    import httpx

    plain_text = html_to_plain_text(html)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_instruction = (
        "You extract ONLY high-value factual claims from news article text.\n\n"
        "Your goal is to identify claims that are IMPORTANT and SUSPICIOUS enough "
        "to be worth fact-checking.\n\n"
        "A claim is worth extracting ONLY IF:\n"
        "- It alleges wrongdoing, attacks, threats, or hostile actions\n"
        "- OR it describes concrete government or military actions\n"
        "- OR it attributes responsibility or intent to a person, group, or state\n"
        "- OR it could significantly mislead readers if false\n\n"
        "DO NOT extract:\n"
        "- opinions, commentary, or rhetoric\n"
        "- emotional or sensational language without factual content\n"
        "- background information or context-only statements\n"
        "- trivial facts that are not disputed or impactful\n\n"
        "Rules:\n"
        "- Use ONLY the provided text\n"
        "- Do NOT add or infer facts\n"
        "- Do NOT rewrite meaning beyond minimal normalization\n"
        "- Provide exact character offsets into the provided text\n"
        "- Offsets must match the provided text exactly\n"
        "- Extract as FEW claims as possible (quality over quantity)\n"
        "- Output JSON only\n"
        "- Return at most 5 claims (pick the highest-value ones)."
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
                                    "Extract ONLY the most important and suspicious factual claims.\n"
                                    "If a statement is not worth fact-checking, DO NOT extract it.\n"
                                    "Return character offsets referring to THIS text."
                                ),
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
    print("Extracted Claims: ", extracted_claims.claims)
    return extracted_claims


def extract_keywords_from_claim(
        claim: str,
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash",
) -> FactCheckQuery:
    """
    Uses Gemini ONLY to extract search keywords for Google Fact Check Tools API.
    It must not add facts, entities, or opinions.
    """

    import json
    import httpx

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_instruction = (
        "You extract search keywords for the Google Fact Check Tools API.\n"
        "Your task is NOT to judge truth, NOT to explain, and NOT to add context.\n"
        "ONLY rewrite the input claim into short keyword queries.\n\n"
        "Rules:\n"
        "- Use ONLY words that already appear in the claim.\n"
        "- Do NOT add new entities, countries, people, or facts.\n"
        "- Do NOT state whether the claim is true or false.\n"
        "- Keep queries short (3–8 words).\n"
        "- Output JSON only."
    )

    response_schema = {
        "type": "object",
        "properties": {
            "primary": {"type": "string"},
            "alternatives": {
                "type": "array",
                "items": {"type": "string"},
            },
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
                                    "Return:\n"
                                    "- primary: the single best keyword query\n"
                                    "- alternatives: 1–3 alternative keyword queries\n"
                                    "Remember: keywords only, no full sentences."
                                ),
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

    with httpx.Client(timeout=15) as client:
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
    print(f"Searching Google Fact Checking Api for keywords ", keywords)

    with httpx.Client(timeout=10) as client:
        params = {
            "query": keywords,
            "pageSize": 10,
            "key": api_key,
        }

        resp = client.get(FACTCHECK_ENDPOINT, params=params)
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

        return claims


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
    confidence: float  # 0.0..1.0 (how strongly supported by the *provided* evidence)
    summary: str  # 1-2 sentences
    reasoning: str  # short explanation, must reference evidence fields
    sources: List[SourceRef]  # ONLY from fact_check_claims reviews
    notes: Optional[str] = None  # e.g. "no matching fact-checks found"


def _facts_to_llm_evidence(fact_check_claims: List[FactCheckClaim]) -> List[dict[str, Any]]:
    """
    Make a compact evidence payload for the LLM (only what we already have).
    """
    evidence: List[dict[str, Any]] = []
    for c in fact_check_claims:
        evidence.append(
            {
                "claim_text": c.text,
                "claimant": c.claimant,
                "claim_date": c.claim_date,
                "reviews": [
                    {
                        "publisher": r.publisher,
                        "publisher_site": r.publisher_site,
                        "title": r.title,
                        "url": r.url,
                        "textual_rating": r.textual_rating,
                        "review_date": r.review_date,
                        "language_code": r.language_code,
                    }
                    for r in c.reviews
                ],
            }
        )
    return evidence


def assert_claim_to_facts(
        claim: str,
        fact_check_claims: List[FactCheckClaim],
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash",
        timeout_s: int = 20,
) -> FactAssertionResult:
    """
    Uses Gemini to decide TRUE/FALSE/UNCLEAR using ONLY:
      - the input claim text
      - the fact-check API results you already fetched (claim text + reviews)

    It must not invent sources. It may return UNCLEAR if:
      - no matching fact-checks
      - ratings are missing/ambiguous
      - multiple sources conflict
      - evidence does not directly address the input claim
    """

    # If you have *zero* evidence, short-circuit without calling the LLM.
    # (You can remove this if you want the LLM to always explain "no evidence".)
    if not fact_check_claims:
        return FactAssertionResult(
            input_claim=claim,
            verdict=Verdict.UNCLEAR,
            confidence=0.0,
            summary="No matching fact-checks were found in the provided results.",
            reasoning="The fact-check result list is empty, so there is no evidence here to confirm or refute the claim.",
            sources=[],
            notes="no_fact_check_results",
        )

    evidence_payload = _facts_to_llm_evidence(fact_check_claims)

    # JSON schema for structured output (Gemini structured outputs)
    response_schema = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["true", "false", "unclear"]},
            "confidence": {"type": "number"},
            "summary": {"type": "string"},
            "reasoning": {"type": "string"},
            "used_sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "publisher": {"type": "string"},
                        "publisher_site": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "review_date": {"type": "string"},
                        "textual_rating": {"type": "string"},
                        "language_code": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "string"},
        },
        "required": ["verdict", "confidence", "summary", "reasoning", "used_sources", "notes"],
    }

    system_instruction = (
        "You are a fact-checking assistant.\n"
        "You must ONLY use the provided evidence (fact-check claims + their claimReview entries).\n"
        "Do NOT use external knowledge. Do NOT invent sources, URLs, publishers, dates, or ratings.\n"
        "If the evidence does not clearly support or refute the input claim, return verdict 'unclear' and explain why.\n"
        "If there are conflicting sources/ratings, return 'unclear' and describe the conflict.\n"
        "When you cite sources, ONLY include sources that appear in the provided evidence reviews."
    )

    user_prompt = {
        "input_claim": claim,
        "evidence": evidence_payload,
        "task": (
            "Decide if the input_claim can be labeled true/false/unclear using ONLY the evidence.\n"
            "Return a structured JSON response that matches the provided schema.\n"
            "Important:\n"
            "- If evidence is about a different claim or not close enough, choose 'unclear'.\n"
            "- Put the exact review entries you relied on into used_sources.\n"
            "- Keep summary short (1-2 sentences). Keep reasoning concise but specific."
        ),
    }

    # Gemini REST endpoint (Google AI for Developers Gemini API)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    body = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [
            {"role": "user", "parts": [{"text": json.dumps(user_prompt, ensure_ascii=False)}]}
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema,
        },
    }

    headers = {
        "Content-Type": "application/json",
        # Prefer header-based auth (avoids key in logs); query-param also works for many setups.
        "x-goog-api-key": gemini_api_key,
    }

    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(f"{resp.status_code}: {resp.text}")

        data = resp.json()

    # Extract the model's JSON text.
    # Typical shape: candidates[0].content.parts[0].text
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected Gemini response shape: {data}")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Gemini did not return valid JSON. Raw text:\n{text}")

    verdict = Verdict(parsed["verdict"])
    confidence = float(parsed["confidence"])
    summary = str(parsed["summary"])
    reasoning = str(parsed["reasoning"])
    notes = parsed.get("notes")

    # Enforce: sources must be subset of evidence reviews (no hallucinated URLs).
    evidence_sources_set = set()
    for c in evidence_payload:
        for r in c["reviews"]:
            evidence_sources_set.add(
                (
                    r.get("publisher"),
                    r.get("publisher_site"),
                    r.get("title"),
                    r.get("url"),
                    r.get("review_date"),
                    r.get("textual_rating"),
                    r.get("language_code"),
                )
            )

    sources: List[SourceRef] = []
    for s in parsed["used_sources"]:
        tup = (
            s.get("publisher"),
            s.get("publisher_site"),
            s.get("title"),
            s.get("url"),
            s.get("review_date"),
            s.get("textual_rating"),
            s.get("language_code"),
        )
        if tup not in evidence_sources_set:
            notes = (notes or "") + " | dropped_invented_source"
            continue

        sources.append(
            SourceRef(
                publisher=s.get("publisher"),
                publisher_site=s.get("publisher_site"),
                title=s.get("title"),
                url=s.get("url"),
                review_date=s.get("review_date"),
                textual_rating=s.get("textual_rating"),
                language_code=s.get("language_code"),
            )
        )

    if not sources:
        return FactAssertionResult(
            input_claim=claim,
            verdict=Verdict.UNCLEAR,
            confidence=0.0,
            summary="No usable sources remained after filtering.",
            reasoning="The model referenced sources that were not present in the provided fact-check evidence, so no supported conclusion can be returned.",
            sources=[],
            notes=(notes or "") + " | no_valid_sources",
        )

    return FactAssertionResult(
        input_claim=claim,
        verdict=verdict,
        confidence=confidence,
        summary=summary,
        reasoning=reasoning,
        sources=sources,
        notes=notes,
    )


def assert_claims_to_facts_batch(
        items: List[CheckedClaim],  # items where span+query+fact_checks already exist, but assertion is not set yet
        *,
        gemini_api_key: str,
        model: str = "gemini-2.5-flash",
        timeout_s: int = 35,
) -> List[FactAssertionResult]:
    """
    Calls Gemini ONCE to decide TRUE/FALSE/UNCLEAR for multiple claims.
    Each item contains:
      - span.claim_text
      - fact_checks (Google Fact Check API results)
    Returns FactAssertionResult list in same order as input items.
    """

    if not items:
        return []

    # Build per-claim evidence payloads
    evidence_payloads: List[List[dict[str, Any]]] = [
        _facts_to_llm_evidence(it.fact_checks) for it in items
    ]

    response_schema = {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "verdict": {"type": "string", "enum": ["true", "false", "unclear"]},
                        "confidence": {"type": "number"},
                        "summary": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "used_sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "publisher": {"type": "string"},
                                    "publisher_site": {"type": "string"},
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "review_date": {"type": "string"},
                                    "textual_rating": {"type": "string"},
                                    "language_code": {"type": "string"},
                                },
                            },
                        },
                        "notes": {"type": "string"},
                    },
                    "required": [
                        "index",
                        "verdict",
                        "confidence",
                        "summary",
                        "reasoning",
                        "used_sources",
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
        "Do NOT use external knowledge. Do NOT invent sources, URLs, publishers, dates, or ratings.\n"
        "If the evidence does not clearly support or refute the input claim, return verdict 'unclear'.\n"
        "If there are conflicting sources/ratings, return 'unclear' and describe the conflict.\n"
        "When you cite sources, ONLY include sources that appear in the provided evidence reviews for that claim.\n"
        "\n"
        "You will receive a list of claims. Return results with the SAME 'index' for each claim.\n"
    )

    user_prompt = {
        "task": (
            "For each item, decide true/false/unclear using ONLY its evidence.\n"
            "Return JSON matching the schema.\n"
            "Important:\n"
            "- If evidence is about a different claim or not close enough, choose 'unclear'.\n"
            "- Put exact review entries you relied on into used_sources.\n"
            "- Keep summary 1-2 sentences. Keep reasoning concise but specific.\n"
        ),
        "items": [
            {
                "index": i,
                "input_claim": items[i].span.claim_text,
                "evidence": evidence_payloads[i],
            }
            for i in range(len(items))
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

    # Build a map index -> parsed result
    by_index: dict[int, dict[str, Any]] = {int(r["index"]): r for r in raw_results}

    results: List[FactAssertionResult] = []
    for i, item in enumerate(items):
        r = by_index.get(i)
        if not r:
            # missing -> treat as unclear
            results.append(
                FactAssertionResult(
                    input_claim=item.span.claim_text,
                    verdict=Verdict.UNCLEAR,
                    confidence=0.0,
                    summary="No result returned for this claim.",
                    reasoning="The batch model output did not include an entry for this claim index.",
                    sources=[],
                    notes="missing_batch_result",
                )
            )
            continue

        verdict = Verdict(r["verdict"])
        confidence = float(r["confidence"])
        summary = str(r["summary"])
        reasoning = str(r["reasoning"])
        notes = r.get("notes")

        # Enforce: used_sources must be subset of THIS claim's evidence reviews
        evidence_sources_set = set()
        for c in evidence_payloads[i]:
            for rr in c["reviews"]:
                evidence_sources_set.add(
                    (
                        rr.get("publisher"),
                        rr.get("publisher_site"),
                        rr.get("title"),
                        rr.get("url"),
                        rr.get("review_date"),
                        rr.get("textual_rating"),
                        rr.get("language_code"),
                    )
                )

        sources: List[SourceRef] = []
        for s in r.get("used_sources", []):
            tup = (
                s.get("publisher"),
                s.get("publisher_site"),
                s.get("title"),
                s.get("url"),
                s.get("review_date"),
                s.get("textual_rating"),
                s.get("language_code"),
            )
            if tup not in evidence_sources_set:
                notes = (notes or "") + " | dropped_invented_source"
                continue
            sources.append(
                SourceRef(
                    publisher=s.get("publisher"),
                    publisher_site=s.get("publisher_site"),
                    title=s.get("title"),
                    url=s.get("url"),
                    review_date=s.get("review_date"),
                    textual_rating=s.get("textual_rating"),
                    language_code=s.get("language_code"),
                )
            )

        if not sources:
            results.append(
                FactAssertionResult(
                    input_claim=item.span.claim_text,
                    verdict=Verdict.UNCLEAR,
                    confidence=0.0,
                    summary="No usable sources remained after filtering.",
                    reasoning="The model referenced sources that were not present in the provided fact-check evidence.",
                    sources=[],
                    notes=(notes or "") + " | no_valid_sources",
                )
            )
            continue

        results.append(
            FactAssertionResult(
                input_claim=item.span.claim_text,
                verdict=verdict,
                confidence=confidence,
                summary=summary,
                reasoning=reasoning,
                sources=sources,
                notes=notes,
            )
        )

    return results


def check_facts_for_html(content_html: str, *, article_id: str) -> FactCheckTrustDTO:
    api_key = os.environ["GEMINI_API_KEY"]

    extracted = extract_claims_from_html(content_html, gemini_api_key=api_key)
    extracted_count = len(extracted.claims)

    dropped_no_evidence = 0
    dropped_keyword_failed = 0
    dropped_assertion_failed = 0

    # Collect candidates that have evidence and are ready for batch assertion
    candidates: List[CheckedClaim] = []

    for span in extracted.claims:
        # keyword query (LLM)
        try:
            query = extract_keywords_from_claim(span.claim_text, gemini_api_key=api_key)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError):
            dropped_keyword_failed += 1
            continue

        # fact-check API search (primary -> alternatives)
        fact_checks = search_for_keywords(query.primary, api_key)
        if not fact_checks:
            for alt in query.alternatives:
                fact_checks = search_for_keywords(alt, api_key)
                if fact_checks:
                    break

        if not fact_checks:
            dropped_no_evidence += 1
            continue

        # assertion will be filled later (batch)
        candidates.append(
            CheckedClaim(
                span=span,
                query=query,
                fact_checks=fact_checks,
                assertion=FactAssertionResult(  # placeholder, replaced after batch
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

    # ✅ ONE model call here
    try:
        assertions = assert_claims_to_facts_batch(candidates, gemini_api_key=api_key)
    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError, RuntimeError):
        # whole batch failed -> drop all candidate assertions
        dropped_assertion_failed += len(candidates)
        candidates = []
        assertions = []

    # Attach assertions back to candidates (keep only those that produced usable sources)
    checked: List[CheckedClaim] = []
    for i, c in enumerate(candidates):
        a = assertions[i] if i < len(assertions) else None
        if not a or not a.sources:
            dropped_assertion_failed += 1
            continue
        c.assertion = a
        checked.append(c)

    checked_count = len(checked)
    dropped_count = extracted_count - checked_count

    dto = FactCheckTrustDTO(
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
            },
        ),
        claims=[_to_claim_dto(article_id, c) for c in checked],
    )
    return dto