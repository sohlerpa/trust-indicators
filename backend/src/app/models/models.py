from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, HttpUrl

from src.modules.tone.tone_classifier import ToneType, ContentType

PublisherType = Literal["public", "private", "unknown"]
Badge = Literal["green", "orange", "red"]


class OwnerInfo(BaseModel):
    owner: str
    percent: float


class ImageProvenance(BaseModel):
    src: str
    c2pa_present: bool
    issuer: Optional[str] = None
    title: Optional[str] = None
    is_ai_generated: bool = False


class TrustIndicators(BaseModel):
    badge: Badge
    fact_checked: bool = False
    tone: Optional[ToneType] = None
    content_type: Optional[ContentType] = None
    tone_type_rationale: Optional[str] = None
    publisher_type: PublisherType = "unknown"
    publisher_country: Optional[str] = None
    c2pa_info: list[ImageProvenance] = None
    owners: list[OwnerInfo] = []


class ArticleRecord(BaseModel):
    id: str
    title: str
    url: HttpUrl
    source: str
    published_at: datetime
    image_url: Optional[HttpUrl] = None
    author: Optional[str] = None
    preview: Optional[str] = ""
    content_html: str


class XPostRecord(BaseModel):
    id: str
    handle: str
    display_name: str
    text: str
    created_at: datetime
