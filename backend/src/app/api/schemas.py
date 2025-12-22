from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from modules.tone.tone_classifier import ContentType, ToneType

PublisherType = Literal["public", "private", "unknown"]
Badge = Literal["green", "orange", "red"]


class TrustIndicators(BaseModel):
    badge: Badge
    fact_checked: bool = False
    tone: Optional[ToneType] = None
    content_type: Optional[ContentType] = None
    publisher_type: PublisherType = "unknown"
    c2pa_present: bool = False


class ArticleSummary(BaseModel):
    id: str
    title: str
    source: str
    published_at: str
    image_url: Optional[str] = None
    trust_indicators: TrustIndicators


class ArticleDetail(ArticleSummary):
    url: Optional[str] = None
    author: Optional[str] = None
    content: str


class XPost(BaseModel):
    id: str
    handle: str
    display_name: str
    text: str
    created_at: str
    indicators: TrustIndicators


class FeedResponse(BaseModel):
    articles: List[ArticleSummary] = Field(default_factory=list)
    x_posts: List[XPost] = Field(default_factory=list)
