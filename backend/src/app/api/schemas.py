from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from src.app.models.models import TrustIndicators

class ArticleBaseOut(BaseModel):
    id: str
    title: str
    preview: Optional[str] = ""
    url: HttpUrl
    source: str
    published_at: datetime
    image_url: Optional[HttpUrl] = None
    author: Optional[str] = None
    content_html: str

class ArticleSummaryOut(BaseModel):
    id: str
    title: str
    preview: Optional[str] = ""
    url: HttpUrl
    source: str
    published_at: datetime
    image_url: Optional[HttpUrl] = None
    trust_indicators: TrustIndicators


class XPostOut(BaseModel):
    id: str
    url: HttpUrl
    text: str
    media_url: Optional[HttpUrl] = None
    created_at: datetime
    indicators: TrustIndicators


class FeedResponse(BaseModel):
    articles: List[ArticleSummaryOut] = Field(default_factory=list)
    x_posts: List[XPostOut] = Field(default_factory=list)


class ArticleIngestIn(BaseModel):
    url: HttpUrl


class ArticleIngestOut(BaseModel):
    id: str
