from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleSummaryOut, XPostOut, ArticleBaseOut
from src.app.models.article import get_or_create_db_trust_indicators, get_fact_check_cache, compute_has_false_facts
from src.app.models.models import ArticleRecord, TrustIndicators, XPostRecord
from src.app.service.trust.badge import compute_badge
from src.modules.tone.tone_classifier import ToneClassification


def compute_trust_indicators_for_xpost(p: XPostRecord, db: Session) -> TrustIndicators:
    """
    Compute trust indicators for an X post.

    Returns:
        TrustIndicators: Computed indicators derived from cached fact-check data
        and a (currently placeholder) tone classification.
    """
    tone_classification = ToneClassification(
        content_type="news",
        tone="neutral",
        confidence=0.0,
        rationale="rationale text",
    )  # classify_tone(p.text) TODO

    fact_check_cache = get_fact_check_cache(db, p.id)

    has_false_facts = compute_has_false_facts(fact_check_cache) if fact_check_cache else None

    return TrustIndicators(
        badge=compute_badge(
            has_false_facts,
            None,
            None,
            None,
            x_mode=True,
            fact_dto=fact_check_cache,
        ),
        fact_checked=False,
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type="unknown",
    )


def to_article_summary_out(
    a: ArticleRecord,
    db,
    feed_mode: bool = True,
) -> ArticleSummaryOut:
    """
    Convert an ArticleRecord into an ArticleSummaryOut with trust indicators.

    Returns:
        ArticleSummaryOut: Summary DTO including cached or computed trust indicators.
    """
    ti = get_or_create_db_trust_indicators(a, db)

    return ArticleSummaryOut(
        id=a.id,
        title=a.title,
        preview=a.preview,
        url=a.url,
        source=a.source,
        published_at=a.published_at,
        image_url=a.image_url,
        trust_indicators=ti,
    )


def to_article_base_out(a) -> ArticleBaseOut:
    """
    Convert an article record into an ArticleBaseOut.

    Returns:
        ArticleBaseOut: DTO containing the full article fields needed by the API.
    """
    return ArticleBaseOut(
        id=a.id,
        title=a.title,
        preview=a.preview,
        url=a.url,
        source=a.source,
        published_at=a.published_at,
        image_url=a.image_url,
        author=a.author,
        content_html=a.content_html,
    )


def to_xpost_out(p: XPostRecord, db: Session) -> XPostOut:
    """
    Convert an XPostRecord into an XPostOut with computed trust indicators.

    Returns:
        XPostOut: DTO including indicators computed for this post.
    """
    return XPostOut(
        id=p.id,
        url=p.url,
        text=p.text,
        media_url=p.media_url,
        created_at=p.created_at,
        indicators=compute_trust_indicators_for_xpost(p, db),
    )