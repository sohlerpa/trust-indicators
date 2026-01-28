import json
from datetime import datetime
from typing import Optional, Any
from urllib.parse import urlparse

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base

from src.app.models.models import ArticleRecord, AuthorExpertise
from src.app.models.models import TrustIndicators
from src.app.service.trust.badge import compute_badge
from src.app.service.trust.publisher import analyze_publisher
from src.modules.fact_checking.fact_checking import FactCheckTrustDTO
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
    print("inserting analysis to db...")
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
        ON CONFLICT (article_id) DO NOTHING
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

def get_or_create_db_trust_indicators(
    article: ArticleRecord,
    db: Session,
) -> TrustIndicators:
    row = get_article_llm_analysis(db, article.id)

    publisher = analyze_publisher(article, db)
    publisher_type = publisher.get("publisher_type")
    publisher_country = getattr(publisher, "publisher_country", None)

    # FAST PATH — tone already cached
    if row and row.tone and row.content_type:
        print("getting data from db...")
        has_false_facts = getattr(row, "has_false_facts", None)

        return TrustIndicators(
            badge=compute_badge(has_false_facts, row.author_label, row.c2pa_present, publisher_type),
            fact_checked=row.fact_checked,
            tone=row.tone,
            content_type=row.content_type,
            tone_type_rationale=row.tone_type_rationale,
            author_expertise=(
                None
                if not row.author_label
                else AuthorExpertise(
                    label=row.author_label,
                    confidence=float(row.author_confidence or 0),
                    author=row.author_name,
                    field=row.author_field,
                    explanation=row.author_explanation,
                )
            ),
            has_false_facts=has_false_facts,
            c2pa_present=row.c2pa_present,
            publisher_type=publisher_type,
            publisher_country=publisher_country,
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
            c2pa_info=[]
        )

    ti = TrustIndicators(
        badge=compute_badge(None, None, None, publisher_type),
        fact_checked=False,
        tone=tone.tone,
        content_type=tone.content_type,
        tone_type_rationale=tone.rationale,
        author_expertise=None,
        c2pa_info=[],
        publisher_type=publisher_type,
        publisher_country=publisher_country,
    )

    insert_article_llm_analysis(db, article.id, ti)
    db.commit()

    return ti


def extract_source(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc

def save_author_expertise(
    db: Session,
    article_id: str,
    ae: AuthorExpertise,
):
    print("save autor expertise to db...")
    db.execute(
        text("""
        INSERT INTO article_llm_analysis (
            article_id,
            author_label,
            author_confidence,
            author_name,
            author_field,
            author_explanation
        )
        VALUES (
            :id, :label, :confidence, :name, :field, :explanation
        )
        ON CONFLICT (article_id)
        DO UPDATE SET
            author_label = EXCLUDED.author_label,
            author_confidence = EXCLUDED.author_confidence,
            author_name = EXCLUDED.author_name,
            author_field = EXCLUDED.author_field,
            author_explanation = EXCLUDED.author_explanation,
            updated_at = now()
        """),
        {
            "id": article_id,
            "label": ae.label,
            "confidence": ae.confidence,
            "name": ae.author,
            "field": ae.field,
            "explanation": ae.explanation,
        },
    )
    db.commit()

def save_tone_analysis(
    db: Session,
    article_id: str,
    tc,
):
    print("save tone analysis to db...")
    db.execute(
        text("""
        INSERT INTO article_llm_analysis (
            article_id,
            tone,
            content_type,
            tone_type_rationale
        )
        VALUES (
            :id, :tone, :ctype, :rationale
        )
        ON CONFLICT (article_id)
        DO UPDATE SET
            tone = EXCLUDED.tone,
            content_type = EXCLUDED.content_type,
            tone_type_rationale = EXCLUDED.tone_type_rationale,
            updated_at = now()
        """),
        {
            "id": article_id,
            "tone": tc.tone,
            "ctype": tc.content_type,
            "rationale": tc.rationale,
        },
    )

    db.commit()


def save_c2pa_present(db: Session, article_id: str, c2pa_present: bool | None):
    print("saving c2pa analysis in db for ", article_id)
    db.execute(
        text("""
             INSERT INTO article_llm_analysis (article_id, c2pa_present)
             VALUES (:id, :present)
             ON CONFLICT (article_id) DO UPDATE SET c2pa_present = EXCLUDED.c2pa_present,
                                                    updated_at   = now()
             """),
        {"id": article_id, "present": c2pa_present},
    )
    db.commit()


def get_fact_check_cache(db: Session, article_id: str) -> Optional[FactCheckTrustDTO]:
    row = db.execute(
        text(
            """
            SELECT result_json
            FROM article_fact_check
            WHERE article_id = :article_id
            """
        ),
        {"article_id": article_id},
    ).mappings().first()

    if not row:
        return None

    payload: Any = row["result_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    return FactCheckTrustDTO(**payload)


def compute_has_false_facts(dto: FactCheckTrustDTO) -> bool:
    claims = getattr(dto, "claims", None) or []
    return any(
        ((c.get("verdict") if isinstance(c, dict) else getattr(c, "verdict", None)) == "false")
        for c in claims
    )


def upsert_fact_check_cache(
        db: Session,
        article_id: str,
        dto: FactCheckTrustDTO,
        *,
        model: Optional[str] = None,
) -> None:
        # 1) Turn dto into a JSON-serializable dict (deep)
    if hasattr(dto, "model_dump"):
        payload = dto.model_dump(mode="json")  # <-- important: converts enums etc.
    else:
        # fallback if dto isn't pydantic
        payload = json.loads(json.dumps(dto, default=lambda o: getattr(o, "__dict__", str(o))))

    # 2) Stats extraction now works on dict
    stats = payload.get("stats") or {}
    extracted = int(stats.get("extractedClaims", 0))
    checked = int(stats.get("checkedClaims", 0))
    dropped = int(stats.get("droppedClaims", 0))

    # 3) Store JSON
    result_json = json.dumps(payload, ensure_ascii=False)

    db.execute(
        text(
            """
            INSERT INTO article_fact_check (
                article_id,
                result_json,
                extracted_claims_count,
                checked_claims_count,
                dropped_claims_count,
                model,
                created_at,
                updated_at
            )
            VALUES (
                       :article_id,
                       (:result_json)::jsonb,
                       :extracted,
                       :checked,
                       :dropped,
                       :model,
                       now(),
                       now()
                   )
                ON CONFLICT (article_id)
        DO UPDATE SET
                result_json = EXCLUDED.result_json,
                               extracted_claims_count = EXCLUDED.extracted_claims_count,
                               checked_claims_count = EXCLUDED.checked_claims_count,
                               dropped_claims_count = EXCLUDED.dropped_claims_count,
                               model = EXCLUDED.model,
                               updated_at = now()
            """
        ),
        {
            "article_id": article_id,
            "result_json": result_json,
            "extracted": extracted,
            "checked": checked,
            "dropped": dropped,
            "model": model,
        },
    )

    has_false = compute_has_false_facts(dto)

    db.execute(
        text("""
             INSERT INTO article_llm_analysis (article_id, has_false_facts)
             VALUES (:article_id, :has_false)
             ON CONFLICT (article_id) DO UPDATE SET
                                                    has_false_facts = EXCLUDED.has_false_facts,
                                                    updated_at = now()
             """),
        {"article_id": article_id, "has_false": has_false},
    )

    db.commit()


def insert_article(
        db: Session,
        *,
        article_id: str,
        title: str,
        url: str,
        published_at: datetime,
        image_url: str | None,
        author: str | None,
        preview: str,
        content_html: str,
) -> None:
    print(f"Inserting article {article_id} into db")
    db.execute(
        text("""
             INSERT INTO articles (
                 id, title, url, published_at, image_url, author, preview, content_html, created_at
             )
             VALUES (
                        :id, :title, :url, :published_at, :image_url, :author, :preview, :content_html, now()
                    )
             """),
        {
            "id": article_id,
            "title": title,
            "url": url,
            "published_at": published_at,
            "image_url": image_url,
            "author": author,
            "preview": preview,
            "content_html": content_html,
        },
    )
    db.commit()