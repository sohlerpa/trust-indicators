import os
import random
import time
from typing import List, Literal, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


# Output structure
class AuthorExpertiseResult(BaseModel):
    author: str
    article_url: str
    publisher_domain: str
    field: str
    label: str
    confidence: float
    explanation: str



class Step1_FieldMap(BaseModel):
    primary_field: str = Field(description="Main field of expertise implied by the article (e.g., Climate science).")
    subfields: List[str] = Field(description="More specific subfields (e.g., climate attribution, carbon cycle).")
    key_terms: List[str] = Field(description="Key technical terms present / expected for the topic.")
    author_disambiguation_hints: List[str] = Field(description="Hints to disambiguate the author in search (orgs, locations, middle initial, etc.).")
    suggested_search_queries: List[str] = Field(description="8-14 search queries to verify whether the author is a credentialed expert in this field.")


class EvidenceItem(BaseModel):
    claim: str = Field(description="A concrete claim about the author's expertise (affiliation, degree, publications).")
    support_summary: str = Field(description="Why the source supports the claim.")
    source_title: Optional[str] = Field(default=None, description="Title of the supporting source or page.")
    source_url: Optional[str] = Field(default=None, description="URL of the supporting source or page.")
    credibility: Literal["high", "medium", "low"] = Field(description="Credibility of the source (e.g., university page=high; random blog=low).")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence this item is correct.")


class Step3_CredentialCheck(BaseModel):
    author: str
    field: str
    found_person_matches: List[str] = Field(description="Possible matches for the author identity (e.g., 'Dr. X at University Y').")
    is_same_person_likely: Literal["yes", "no", "uncertain"] = Field(description="Whether evidence likely refers to the same author (name collisions are common).")
    evidence: List[EvidenceItem] = Field(description="Evidence items grounded in search.")
    gaps: List[str] = Field(description="What information is missing to be confident (e.g., no verified affiliation).")
    credentialed_expert_assessment: Literal["yes", "no", "uncertain"]
    credentialed_expert_confidence: float = Field(ge=0.0, le=1.0)


class Step2_GroundedNotes(BaseModel):
    notes: str = Field(description="Grounded findings with citations and URLs included inline.")


class Step4_FinalAssessment(BaseModel):
    author: str
    field: str
    credentialed_expert: Literal["yes", "no", "uncertain"]
    credentialed_confidence: float = Field(ge=0.0, le=1.0)

    # Text-only quality signals
    article_expert_like: Literal["yes", "no", "uncertain"] = Field(description="Whether the article reads like it was written by a domain expert (text-only signals).")
    article_quality_confidence: float = Field(ge=0.0, le=1.0)
    rubric_scores: dict = Field(description="A dict of rubric scores 0..1, e.g. {'accuracy':0.8,'use_of_uncertainty':0.6,'use_of_sources':0.4}")
    red_flags: List[str] = Field(description="Potential misconceptions, overclaims, bad reasoning, missing nuance, etc.")
    strengths: List[str] = Field(description="Signals of competence: correct framing, good uncertainty, good sourcing, etc.")

    # Combined decision
    final_label: Literal["field_expert", "not_field_expert", "uncertain"] = Field(description="Combined judgment: field_expert requires external credential evidence; otherwise uncertain.")
    final_confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(description="Short, user-facing explanation of why.")



def _response_text(resp) -> str:
    txt = getattr(resp, "text", None)
    if isinstance(txt, str):
        txt = txt.strip()
        if txt:
            return txt

    candidates = getattr(resp, "candidates", None) or []
    chunks: list[str] = []
    for c in candidates:
        content = getattr(c, "content", None)
        parts = getattr(content, "parts", None) or []
        for p in parts:
            t = getattr(p, "text", None)
            if isinstance(t, str) and t:
                chunks.append(t)
    return "\n".join(chunks).strip()


def _generate_with_retry(
        client,
        *,
        model: str,
        contents: str,
        config,
        max_retries: int = 8,
        base_sleep_s: float = 0.6,
        max_sleep_s: float = 12.0,
):
    """
    Synchronous call that waits for a response.
    Retries transient errors (notably 503 overloaded) with exponential backoff + jitter.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except genai_errors.ServerError as e:
            # 503 UNAVAILABLE / overloaded is transient
            last_exc = e
        except genai_errors.APIError as e:
            # Retry only on likely-transient API errors (5xx / 429)
            last_exc = e
            status = getattr(e, "status_code", None)
            if status is not None and status < 500 and status != 429:
                raise  # don't retry non-transient 4xx

        # backoff + jitter
        sleep = min(max_sleep_s, base_sleep_s * (2 ** attempt))
        sleep = sleep * (0.7 + 0.6 * random.random())  # jitter in [0.7, 1.3]
        time.sleep(sleep)

    raise RuntimeError(f"Gemini generate_content failed after {max_retries} retries") from last_exc


def assess_author_expertise(
        text: str,
        author: str,
        article_url: str,
        model: str = "gemini-2.5-flash",
        api_key_env: str = "GEMINI_API_KEY",
        debug: bool = False,
) -> AuthorExpertiseResult:

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("author must be a non-empty string")
    if not isinstance(article_url, str) or not article_url.strip():
        raise ValueError("article_url must be a non-empty string")

    article_url = article_url.strip()
    parsed = urlparse(article_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"article_url must be a valid http(s) URL, got: {article_url}")

    publisher_domain = parsed.netloc.lower()
    if publisher_domain.startswith("www."):
        publisher_domain = publisher_domain[4:]

    if not os.getenv(api_key_env):
        raise EnvironmentError(f"Missing environment variable {api_key_env}")
    client = genai.Client()


    # ---- Step 1: Field map + search queries
    prompt1 = f"""
    You are helping determine whether an article's author is an expert in the article's field.
    
    Given:
    - Author name: {author}
    - Publisher domain (derived): {publisher_domain}
    - Article URL: {article_url}
    - Article text: <<<BEGIN TEXT
    {text}
    END TEXT>>>
    
    Task:
    1) Identify the primary field and 2-6 plausible subfields.
    2) Extract 8-20 key technical terms you would expect in expert writing on this topic.
    3) Provide 3-8 author disambiguation hints that would help identify the correct person online.
    4) Provide 8-14 Google search queries to verify whether this author is credentialed in the identified field.
    
    Rules for queries:
    - Include at least 4 queries that are site-restricted to the publisher domain:
      e.g., site:{publisher_domain} "{author}", author page, Autoren, Redaktion, Impressum.
    - Include queries for author profile pages, author archives, and byline pages.
    - Include ORCID / Google Scholar queries only if the author seems academic; otherwise prioritize journalist bio evidence.
    
    Return ONLY valid JSON that matches the schema.
    """.strip()

    response1 = _generate_with_retry(
        client,
        model=model,
        contents=prompt1,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": Step1_FieldMap.model_json_schema(),
        },
    )
    step1 = Step1_FieldMap.model_validate_json(_response_text(response1))
    if debug:
        print(f"Step1:\n{step1}\n")


    # ---- Step 2: Grounded evidence memo
    grounding_tool = types.Tool(google_search=types.GoogleSearch())

    prompt2 = f"""
    You are verifying whether an author is a credentialed expert in a field, using web evidence.
    
    Author: {author}
    Field: {step1.primary_field}
    Subfields: {step1.subfields}
    Publisher domain: {publisher_domain}
    Article URL: {article_url}
    
    Priority order:
    1) Find the article URL and extract any author bio/byline info and links to author profile pages.
    2) Find author archive/profile pages on the publisher domain:
       site:{publisher_domain} "{author}", Autoren, Redaktion, Impressum.
    3) Then expand to broader web sources (LinkedIn, ORCID, university pages, etc.) ONLY if needed.
    
    Rules:
    - Name collisions are common: explicitly discuss whether results refer to the same person.
    - Prefer high-credibility sources.
    - Include URLs whenever possible.
    - If you cannot verify credentials, say so (don't guess).
    
    Suggested queries (you may use or adapt):
    {step1.suggested_search_queries}
    
    Write a concise evidence memo with bullet points and URLs.
    """.strip()

    resp2 = _generate_with_retry(
        client,
        model=model,
        contents=prompt2,
        config=types.GenerateContentConfig(tools=[grounding_tool]),
    )
    grounded_notes = _response_text(resp2)
    if not grounded_notes:
        grounded_notes = "No grounded memo text returned by the model."
    if debug:
        print(f"Grounded memo:\n{grounded_notes}\n")


    # ---- Step 3: Memo into strict JSON
    prompt3 = f"""
    Convert the following evidence memo into JSON that matches the schema precisely.
    
    Author: {author}
    Field: {step1.primary_field}
    Publisher domain: {publisher_domain}
    Article URL: {article_url}
    
    EVIDENCE MEMO:
    <<<BEGIN MEMO
    {grounded_notes}
    END MEMO>>>
    
    Instructions:
    - Treat matches on the publisher domain (author page / editorial staff page / author archive) as strong identity evidence.
    - Fill found_person_matches with short disambiguating descriptors.
    - Include evidence items with claim/support_summary/source_title/source_url/credibility/confidence.
    - If URL/title is missing, use null.
    - Be conservative: if not sure, use "uncertain".
    Return ONLY valid JSON.
    """.strip()

    response3 = _generate_with_retry(
        client,
        model=model,
        contents=prompt3,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": Step3_CredentialCheck.model_json_schema(),
        },
    )
    step3 = Step3_CredentialCheck.model_validate_json(_response_text(response3))
    if debug:
        print(f"Step3:\n{step3}\n")


    # ---- Step 4: Final assessment
    prompt4 = f"""
    You are producing a final assessment: Is the author an expert in the field?
    
    Separate:
    (A) "Credentialed expert" (verified external evidence)
    (B) "Expert-like article" (text-only signals)
    
    Inputs:
    - Author: {author}
    - Field: {step1.primary_field}
    - Article text: <<<BEGIN TEXT
    {text}
    END TEXT>>>
    
    Credential evidence summary:
    {step3.model_dump_json(indent=2)}
    
    Rubric (score each 0..1, put into rubric_scores):
    - accuracy_and_correct_framing
    - handling_of_uncertainty_and_limits
    - use_of_primary_sources_or_reputable_refs (based only on what appears in the text)
    - domain_specificity_and_precision
    - avoidance_of_common_misconceptions
    - internal_consistency
    
    Rules:
    - If credential evidence is "yes" with decent confidence, final_label can be "field_expert".
    - If credential evidence is "no" BUT there is strong evidence the author is the publisher's specialist reporter/editor
      for this field (e.g., author page shows beat like finance/pensions), final_label may be "field_expert" (journalistic expertise).
      Otherwise keep "not_field_expert".
    - If credential evidence is "uncertain", final_label should usually be "uncertain" (unless the text clearly indicates non-expertise).
    
    Keep explanation short and practical.
    Return ONLY valid JSON that matches the schema.
    """.strip()

    response4 = _generate_with_retry(
        client,
        model=model,
        contents=prompt4,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": Step4_FinalAssessment.model_json_schema(),
        },
    )
    step4 = Step4_FinalAssessment.model_validate_json(_response_text(response4))
    if debug:
        print(f"Step4:\n{step4}\n")

    return AuthorExpertiseResult(
        author=author,
        article_url=article_url,
        publisher_domain=publisher_domain,
        field=step4.field,
        label=step4.final_label,
        confidence=step4.final_confidence,
        explanation=step4.explanation
    )
