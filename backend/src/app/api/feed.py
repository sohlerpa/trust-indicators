from typing import List, Optional, Literal, Dict

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from src.app.api.schemas import FeedResponse, ArticleSummaryOut, XPostOut
from src.app.data.sample_data import X_POSTS
from src.app.models.article import get_all_articles, get_fact_check_cache
from src.app.service.article_mapper import to_article_summary_out, to_xpost_out
from src.app.service.db_connector import get_db

router = APIRouter()

AuthorExpertFilter = Literal["field_expert", "not_field_expert", "unknown"]


@router.get("/feed", response_model=FeedResponse)
def get_feed(
        fact_checked: Optional[bool] = None,
        tone: Optional[List[str]] = Query(default=None),
        content_type: Optional[List[str]] = Query(default=None),
        publisher_type: Optional[List[str]] = Query(default=None),
        no_false_facts: Optional[bool] = None,
        author_expert: Optional[AuthorExpertFilter] = None,
        c2pa_present: Optional[bool] = None,
        db: Session = Depends(get_db),
):
    articles_raw = get_all_articles(db)
    x_raw = X_POSTS

    # enrich with trust indicators
    articles: list[ArticleSummaryOut] = [to_article_summary_out(a, db, feed_mode=True) for a in articles_raw]
    x_posts: list[XPostOut] = [to_xpost_out(p) for p in x_raw]

    # Precompute "has false verdict"
    has_false_by_id: Dict[str, Optional[bool]] = {}
    if no_false_facts is not None:
        for a in articles:
            dto = get_fact_check_cache(db, a.id)
            if dto is None:
                has_false_by_id[a.id] = None
            else:
                claims = getattr(dto, "claims", None) or []
                has_false_by_id[a.id] = any(
                    ((c.get("verdict") if isinstance(c, dict) else getattr(c, "verdict", None)) == "false")
                    for c in claims
                )

    def matches(article: ArticleSummaryOut) -> bool:
        ti = article.trust_indicators

        if fact_checked is not None and ti.fact_checked != fact_checked:
            return False
        if tone and (ti.tone not in tone):
            return False
        if content_type and (ti.content_type not in content_type):
            return False
        if publisher_type and (ti.publisher_type not in publisher_type):
            return False

        # no_false_facts
        if no_false_facts is not None:
            has_false = has_false_by_id.get(article.id)
            if has_false is None:
                return False
            if no_false_facts is True and has_false is True:
                return False
            if no_false_facts is False and has_false is False:
                return False

        # author expert
        if author_expert is not None:
            label = "unknown"
            ae = getattr(ti, "author_expertise", None)
            if ae is not None and getattr(ae, "label", None):
                label = ae.label
            if label != author_expert:
                return False

        # c2pa_present
        if c2pa_present is not None:
            if bool(getattr(ti, "c2pa_present", False)) != c2pa_present:
                return False

        return True

    return FeedResponse(
        articles=[a for a in articles if matches(a)],
        x_posts=[p for p in x_posts],
    )