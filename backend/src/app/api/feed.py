from fastapi import APIRouter, Query
from typing import List, Optional
from app.api.schemas import FeedResponse, ArticleSummary, XPost
from app.data.sample_data import article_summaries, X_POSTS

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
        fact_checked: Optional[bool] = None,
        tone: Optional[List[str]] = Query(default=None),
        content_type: Optional[List[str]] = Query(default=None),
        publisher_type: Optional[List[str]] = Query(default=None),
):
    articles = article_summaries()
    x_posts = X_POSTS

    # TODO here, we have to run the checks on the articles (enrich it with trust indicators)
    # TODO maybe we can filter for something already or do some pre processing that we don't have to run everything on all posts/articles?

    def matches(ind):
        if fact_checked is not None and ind.fact_checked != fact_checked:
            return False
        if tone and (ind.tone not in tone):
            return False
        if content_type and (ind.content_type not in content_type):
            return False
        if publisher_type and (ind.publisher_type not in publisher_type):
            return False
        return True

    filtered_articles: list[ArticleSummary] = [a for a in articles if matches(a.trust_indicators)]
    filtered_x: list[XPost] = [p for p in x_posts if matches(p.indicators)]

    return FeedResponse(articles=filtered_articles, x_posts=filtered_x)
