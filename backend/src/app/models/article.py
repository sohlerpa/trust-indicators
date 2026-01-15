from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from src.app.models.models import ArticleRecord


Base = declarative_base()


class ArticleDB(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    author = Column(Text)
    published_at = Column(TIMESTAMP, nullable=False)
    image_url = Column(Text)
    preview = Column(Text)
    content_html = Column(Text)

def get_all_articles(db: Session) -> list[ArticleRecord]:
    rows = db.query(ArticleDB).order_by(ArticleDB.published_at.desc()).all()

    return [
        ArticleRecord(
            id=r.id,
            title=r.title,
            source=extract_source(r.url),
            published_at=r.published_at,
            image_url=r.image_url,
            url=r.url,
            author=r.author,
            preview=r.preview,
            content_html=r.content_html,
        )
        for r in rows
    ]

def extract_source(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc