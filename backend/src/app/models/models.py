from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, HttpUrl

from src.modules.author_expertise.author_expertise_classifier import AuthorExpertiseResult
from src.modules.tone.tone_classifier import ToneType, ContentType

PublisherType = Literal["public", "private", "unknown"]
Badge = Literal["green", "orange", "red", "grey"]


class OwnerInfo(BaseModel):
    owner: str
    percent: float


class ImageProvenance(BaseModel):
    src: str
    c2pa_present: bool
    issuer: Optional[str] = None
    title: Optional[str] = None
    is_ai_generated: bool = False

class AuthorExpertise(BaseModel):
    label: str
    confidence: float
    author: Optional[str] = None
    field: Optional[str] = None
    explanation: Optional[str] = None


class TrustIndicators(BaseModel):
    badge: str
    fact_checked: bool | None = None
    tone: str | None = None
    content_type: str | None = None
    tone_type_rationale: str | None = None

    author_expertise: Optional[AuthorExpertise] = None

    c2pa_info: list[ImageProvenance] = []
    owners: list[OwnerInfo] = []
    publisher_type: str | None = None
    publisher_country: str | None = None


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
    url: HttpUrl
    text: str
    media_url: Optional[HttpUrl] = None
    created_at: datetime
