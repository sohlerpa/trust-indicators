from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse
from sqlalchemy import text

from sqlalchemy.orm import Session
from src.app.models.models import ArticleRecord

from src.app.models.models import TrustIndicators, ImageProvenance
from src.modules.tone.tone_classifier import classify_tone

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
    created_at = Column(TIMESTAMP, nullable=False)

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
            created_at=r.created_at,
        )
        for r in rows
    ]

def get_article_by_id(db: Session, article_id: str) -> ArticleRecord | None:
    row = db.execute(
        text("""
        SELECT
            id,
            title,
            url,
            published_at,
            image_url,
            author,
            preview,
            content_html
        FROM articles
        WHERE id = :id
        """),
        {"id": article_id},
    ).fetchone()

    if not row:
        return None

    return ArticleRecord(
        id=row.id,
        title=row.title,
        url=row.url,
        source=extract_source(row.url),
        published_at=row.published_at,
        image_url=row.image_url,
        author=row.author,
        preview=row.preview or "",
        content_html=row.content_html,
    )

def get_article_llm_analysis(db: Session, article_id: str):
    return db.execute(
        text("SELECT * FROM article_llm_analysis WHERE article_id = :id"),
        {"id": article_id},
    ).fetchone()

def insert_article_llm_analysis(db: Session, article_id: str, ti: TrustIndicators):
    db.execute(
        text("""
        INSERT INTO article_llm_analysis (
            article_id,
            badge,
            fact_checked,
            tone,
            content_type,
            tone_type_rationale
        ) VALUES (
            :article_id,
            :badge,
            :fact_checked,
            :tone,
            :content_type,
            :rationale
        )
        """),
        {
            "article_id": article_id,
            "badge": ti.badge,
            "fact_checked": ti.fact_checked,
            "tone": ti.tone,
            "content_type": ti.content_type,
            "rationale": ti.tone_type_rationale,
        },
    )

def insert_c2pa_assets(db: Session, article_id: str, assets: list[ImageProvenance]):
    for a in assets:
        db.execute(
            text("""
            INSERT INTO article_c2pa_assets (
                article_id, src, c2pa_present, issuer, title, is_ai_generated
            ) VALUES (
                :article_id, :src, :present, :issuer, :title, :ai
            )
            """),
            {
                "article_id": article_id,
                "src": a.src,
                "present": a.c2pa_present,
                "issuer": a.issuer,
                "title": a.title,
                "ai": a.is_ai_generated,
            },
        )

def get_or_create_trust_indicators(
    article: ArticleRecord,
    db: Session,
) -> TrustIndicators:
    row = get_article_llm_analysis(db, article.id)

    if row:
        print(f"using cached analysis from DB for article {article.id}")
        # FAST PATH (no LLM, no C2PA)
        c2pa_rows = db.execute(
            text("SELECT * FROM article_c2pa_assets WHERE article_id = :id"),
            {"id": article.id},
        ).fetchall()

        return TrustIndicators(
            badge=row.badge,
            fact_checked=row.fact_checked,
            tone=row.tone,
            content_type=row.content_type,
            tone_type_rationale=row.tone_type_rationale,
            c2pa_info=[
                ImageProvenance(
                    src=r.src,
                    c2pa_present=r.c2pa_present,
                    issuer=r.issuer,
                    title=r.title,
                    is_ai_generated=r.is_ai_generated,
                )
                for r in c2pa_rows
            ],
        )

    # SLOW PATH (first time only)
    print(f"generating new analysis for article {article.id}")
    tone = classify_tone(article.content_html)

    if tone.tone == "error" or tone.content_type == "error":
        return TrustIndicators(
            badge="red",
            fact_checked=False,
            tone=None,
            content_type=None,
            tone_type_rationale=None,
        )    #c2pa_assets = extract_and_check_c2pa(article.content_html)

    ti = TrustIndicators(
        badge="red",  # temp
        fact_checked=False,
        tone=tone.tone,
        content_type=tone.content_type,
        tone_type_rationale=tone.rationale,
        #c2pa_info=c2pa_assets,
    )

    if tone.tone != "error" and tone.content_type != "error":
        insert_article_llm_analysis(db, article.id, ti)
        db.commit()

    #insert_c2pa_assets(db, article.id, c2pa_assets)
    #db.commit()

    return ti



def load_article_c2pa_assets(db: Session, article_id: str):
    return db.execute(
        text("""
        SELECT *
        FROM article_c2pa_assets
        WHERE article_id = :id
        ORDER BY id
        """),
        {"id": article_id},
    ).fetchall()

def extract_source(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc