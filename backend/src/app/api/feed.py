from fastapi import APIRouter, Query
from typing import List, Optional

from src.app.api.schemas import FeedResponse, ArticleSummaryOut, XPostOut
from src.app.data.sample_data import X_POSTS, ARTICLES
from src.app.service.trust_indicator_enricher import to_article_summary_out, to_xpost_out

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
        fact_checked: Optional[bool] = None,
        tone: Optional[List[str]] = Query(default=None),
        content_type: Optional[List[str]] = Query(default=None),
        publisher_type: Optional[List[str]] = Query(default=None),
):
    # TODO maybe we can filter for something already or do some pre processing that we don't have to run everything on all posts/articles?

    articles_raw = ARTICLES
    x_raw = X_POSTS

    # enrich with trust indicators
    articles: list[ArticleSummaryOut] = [to_article_summary_out(a) for a in articles_raw]
    x_posts: list[XPostOut] = [to_xpost_out(p) for p in x_raw]

    def matches(ind) -> bool:
        if fact_checked is not None and ind.fact_checked != fact_checked:
            return False
        if tone and (ind.tone not in tone):
            return False
        if content_type and (ind.content_type not in content_type):
            return False
        if publisher_type and (ind.publisher_type not in publisher_type):
            return False
        return True

    return FeedResponse(
        articles=[a for a in articles if matches(a.trust_indicators)],
        x_posts=[p for p in x_posts if matches(p.indicators)],
    )
