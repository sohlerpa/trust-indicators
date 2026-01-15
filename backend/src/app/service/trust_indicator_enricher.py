from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleSummaryOut, ArticleDetailOut, XPostOut
from src.app.models.models import ArticleRecord, TrustIndicators, XPostRecord, OwnerInfo
from src.modules.source_funding.queries import GET_DOMAIN_OWNERS, GET_DOMAIN_PUBLISHER_TYPE
from src.modules.tone.tone_classifier import classify_tone


def compute_trust_indicators_for_article(a: ArticleRecord, db: Session) -> TrustIndicators:
    tone_classification = classify_tone(a.content_html)
    owners_db_result = db.execute(GET_DOMAIN_OWNERS, {"domain": a.source}).fetchall()
    owners = [
        OwnerInfo(owner=row.name, percent=float(row.ownership_percent))
        for row in owners_db_result
    ]

    publisher_type_db_result = db.execute(GET_DOMAIN_PUBLISHER_TYPE, {"domain": a.source}).fetchone()
    publisher_type = (
        publisher_type_db_result.publisher_type
        if publisher_type_db_result
        else "unknown"
    )

    return TrustIndicators(
        badge="red",  # TODO
        fact_checked=False,  # TODO
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type=publisher_type,
        c2pa_present=False,  # TODO
        owners=owners
    )


def compute_trust_indicators_for_xpost(p: XPostRecord) -> TrustIndicators:
    tone_classification = classify_tone(p.text)
    return TrustIndicators(
        badge="red",  # TODO
        fact_checked=False,  # TODO
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type="unknown",  # TODO
        c2pa_present=False,  # TODO
    )


def to_article_summary_out(a: ArticleRecord, db: Session) -> ArticleSummaryOut:
    return ArticleSummaryOut(
        id=a.id,
        title=a.title,
        url=a.url,
        source=a.source,
        published_at=a.published_at,
        image_url=a.image_url,
        trust_indicators=compute_trust_indicators_for_article(a, db),
    )


def to_article_detail_out(a: ArticleRecord, db: Session) -> ArticleDetailOut:
    base = to_article_summary_out(a, db)
    return ArticleDetailOut(
        **base.model_dump(),
        author=a.author,
        content_html=a.content_html,
    )


def to_xpost_out(p: XPostRecord) -> XPostOut:
    return XPostOut(
        id=p.id,
        handle=p.handle,
        display_name=p.display_name,
        text=p.text,
        created_at=p.created_at,
        indicators=compute_trust_indicators_for_xpost(p),
    )
