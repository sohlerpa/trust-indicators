from urllib.parse import urljoin

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleSummaryOut, ArticleDetailOut, XPostOut
from src.app.models.models import ArticleRecord, TrustIndicators, XPostRecord, OwnerInfo, ImageProvenance
from src.modules.author_expertise.author_expertise_classifier import assess_author_expertise
from src.modules.provenance_media.extractor import c2pa_for_image_url
from src.modules.source_funding.queries import GET_DOMAIN_OWNERS, GET_DOMAIN_PUBLISHER_TYPE
from src.modules.tone.tone_classifier import classify_tone, ToneClassification
from src.app.models.article import get_or_create_db_trust_indicators


def extract_img_srcs(content_html: str, article_url: str, api_base_url: str, main_image_url: str=None) -> list[str]:
    """
    - Absolute URLs (https://...) stay as-is
    - Root-relative paths are resolved against api_base_url
      (so /assets/... -> http://localhost:8000/assets/...)
    """
    soup = BeautifulSoup(content_html or "", "html.parser")
    srcs: list[str] = []

    if main_image_url:
        srcs.append(main_image_url)

    for img in soup.find_all(["img", "iframe"]):
        src = (img.get("src") or "").strip()
        if not src:
            continue

        if src.startswith(("http://", "https://")):
            resolved = src
        elif src.startswith("/"):
            resolved = urljoin(api_base_url, src)
        else:
            resolved = urljoin(article_url, src)

        srcs.append(resolved)

    return srcs


def compute_trust_indicators_for_article(a: ArticleRecord, db: Session, feed_mode=True) -> TrustIndicators:
    tone_classification = classify_tone(a.content_html)
    owners_db_result = db.execute(GET_DOMAIN_OWNERS, {"domain": a.source}).fetchall()
    owners = [
        OwnerInfo(owner=row.name, percent=float(row.ownership_percent))
        for row in owners_db_result
    ]

    publisher_type_db_result = db.execute(
        GET_DOMAIN_PUBLISHER_TYPE,
        {"domain": a.source}
    ).fetchone()

    publisher_type = publisher_type_db_result.publisher_type if publisher_type_db_result else "unknown"
    publisher_country = publisher_type_db_result.country if publisher_type_db_result else None

    img_urls = extract_img_srcs(a.content_html, article_url=str(a.url), api_base_url="http://localhost:8000", main_image_url=str(a.image_url))
    images: list[ImageProvenance] = []
    for u in img_urls:
        info = c2pa_for_image_url(u)
        if not info: continue
        images.append(
            ImageProvenance(
                src=u,
                c2pa_present=info.manifest_found,
                issuer=info.issuer,
                title=info.title,
                is_ai_generated=info.is_ai_generated,
            )
        )

    if feed_mode: # if called in the feed
        author_expertise = None
    else: # if called by a single article
        author_expertise = assess_author_expertise(a.content_html, a.author, str(a.url))

    return TrustIndicators(
        badge="red",  # TODO
        fact_checked=False,  # TODO
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type=publisher_type,
        publisher_country=publisher_country,
        c2pa_info=images,
        owners=owners,
        author_expertise=author_expertise,
    )

def enrich_trust_indicators_for_article(
    ti: TrustIndicators,
    a: ArticleRecord,
    db: Session,
    feed_mode: bool = True,
) -> TrustIndicators:
    owners_db_result = db.execute(GET_DOMAIN_OWNERS, {"domain": a.source}).fetchall()
    ti.owners = [
        OwnerInfo(owner=row.name, percent=float(row.ownership_percent))
        for row in owners_db_result
    ]

    publisher_type_db_result = db.execute(
        GET_DOMAIN_PUBLISHER_TYPE,
        {"domain": a.source}
    ).fetchone()

    ti.publisher_type = (
        publisher_type_db_result.publisher_type
        if publisher_type_db_result
        else "unknown"
    )
    ti.publisher_country = (
        publisher_type_db_result.country
        if publisher_type_db_result
        else None
    )

    img_urls = extract_img_srcs(
        a.content_html,
        article_url=str(a.url),
        api_base_url="http://localhost:8000",
    )

    ti.c2pa_info = [
        ImageProvenance(
            src=u,
            c2pa_present=info.manifest_found,
            issuer=info.issuer,
            title=info.title,
            is_ai_generated=info.is_ai_generated,
        )
        for u in img_urls
        for info in [c2pa_for_image_url(u)]
    ]

    if not feed_mode:
        ti.author_expertise = assess_author_expertise(
            a.content_html, a.author, str(a.url)
        )

    return ti


def compute_trust_indicators_for_xpost(p: XPostRecord) -> TrustIndicators:
    tone_classification = ToneClassification(content_type="news", tone="neutral", confidence=0.0, rationale="rationale text") #classify_tone(p.text) TODO
    return TrustIndicators(
        badge="red",  # TODO
        fact_checked=False,  # TODO
        tone=tone_classification.tone,
        content_type=tone_classification.content_type,
        tone_type_rationale=tone_classification.rationale,
        publisher_type="unknown",  # TODO
    )


def to_article_summary_out(a: ArticleRecord, db: Session, feed_mode=True) -> ArticleSummaryOut:
    ti = get_or_create_db_trust_indicators(a, db)
    ti = enrich_trust_indicators_for_article(ti, a, db, feed_mode)

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


def to_article_detail_out(a: ArticleRecord, db: Session, feed_mode=True) -> ArticleDetailOut:
    base = to_article_summary_out(a, db, feed_mode=feed_mode)
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
