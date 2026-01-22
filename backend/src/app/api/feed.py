from fastapi import APIRouter, Query, Depends
from typing import List, Optional

from sqlalchemy.orm import Session

from src.app.api.articles import get_publisher
from src.app.api.schemas import FeedResponse, ArticleSummaryOut, XPostOut
from src.app.data.sample_data import X_POSTS
from src.app.models.article import get_all_articles
from src.app.service.article_mapper import to_article_summary_out, to_xpost_out
from src.app.service.db_connector import get_db

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
        fact_checked: Optional[bool] = None,
        tone: Optional[List[str]] = Query(default=None),
        content_type: Optional[List[str]] = Query(default=None),
        publisher_type: Optional[List[str]] = Query(default=None),
        db: Session = Depends(get_db)
):

    articles_raw = get_all_articles(db)
    x_raw = X_POSTS

    # enrich with trust indicators
    articles: list[ArticleSummaryOut] = [to_article_summary_out(a, db, feed_mode=True) for a in articles_raw]
    x_posts: list[XPostOut] = [to_xpost_out(p) for p in x_raw]

    def matches(article: ArticleSummaryOut) -> bool:
        if fact_checked is not None and article.trust_indicators.fact_checked != fact_checked:
            return False
        if tone and (article.trust_indicators.tone not in tone):
            return False
        if content_type and (article.trust_indicators.content_type not in content_type):
            return False
        if publisher_type and (get_publisher(article.id, db)["publisher_type"] not in publisher_type):
            return False
        return True

    return FeedResponse(
        articles=[a for a in articles if matches(a)],
        x_posts=[p for p in x_posts],
    )
