from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from src.app.models.models import TrustIndicators


class ArticleSummaryOut(BaseModel):
    id: str
    title: str
    preview: Optional[str] = ""
    url: HttpUrl
    source: str
    published_at: datetime
    image_url: Optional[HttpUrl] = None
    trust_indicators: TrustIndicators


class ArticleDetailOut(ArticleSummaryOut):
    author: Optional[str] = None
    content_html: str


class XPostOut(BaseModel):
    id: str
    handle: str
    display_name: str
    text: str
    created_at: datetime
    indicators: TrustIndicators


class FeedResponse(BaseModel):
    articles: List[ArticleSummaryOut] = Field(default_factory=list)
    x_posts: List[XPostOut] = Field(default_factory=list)
