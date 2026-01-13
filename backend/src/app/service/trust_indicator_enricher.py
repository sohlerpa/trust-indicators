from src.app.api.schemas import ArticleSummaryOut, ArticleDetailOut, XPostOut
from src.app.models.models import ArticleRecord, TrustIndicators, XPostRecord
from src.modules.tone.tone_classifier import classify_tone


def compute_trust_indicators_for_article(a: ArticleRecord) -> TrustIndicators:
    tone_classification = classify_tone(a.content_html)
    return TrustIndicators(
        badge="red",  # TODO
        fact_checked=False,  # TODO
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type="private",  # TODO
        c2pa_present=False,  # TODO
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


def to_article_summary_out(a: ArticleRecord) -> ArticleSummaryOut:
    return ArticleSummaryOut(
        id=a.id,
        title=a.title,
        url=a.url,
        source=a.source,
        published_at=a.published_at,
        image_url=a.image_url,
        trust_indicators=compute_trust_indicators_for_article(a),
    )


def to_article_detail_out(a: ArticleRecord) -> ArticleDetailOut:
    base = to_article_summary_out(a)
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
