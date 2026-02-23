import threading
import time
from sqlalchemy.orm import Session

from src.app.models.article import get_article_llm_analysis, save_author_expertise
from src.app.models.models import AuthorExpertise
from src.app.service.progress import ProgressFn
from src.modules.author_expertise.author_expertise_classifier import assess_author_expertise


def analyze_author(
    article,
    db: Session,
    progress: ProgressFn | None = None,
) -> AuthorExpertise | None:
    """
    Analyze and cache author expertise for an article.

    Returns:
        AuthorExpertise | None: Cached or newly computed expertise, or None on failure.
    """
    if progress:
        progress("start", 0.05)

    row = get_article_llm_analysis(db, article.id)

    if row and row.author_label:
        if progress:
            progress("done", 1.0)

        return AuthorExpertise(
            label=row.author_label,
            confidence=float(row.author_confidence or 0),
            author=row.author_name,
            field=row.author_field,
            explanation=row.author_explanation,
        )

    stop_flag = False

    def progress_ticker() -> None:
        """
        Periodically increase progress while classification runs.

        Returns:
            None
        """
        pct = 0.35
        while not stop_flag and pct < 0.80:
            time.sleep(3)
            pct += 0.03
            if progress:
                progress("analyzing_author", round(pct, 3))

    if progress:
        progress("analyze_author", 0.35)

    t = threading.Thread(target=progress_ticker, daemon=True)
    t.start()

    ae = assess_author_expertise(
        article.content_html,
        article.author,
        str(article.url),
    )

    stop_flag = True
    t.join(timeout=0.1)

    if not ae or ae.label == "error":
        if progress:
            progress("done", 1.0)
        return None

    if progress:
        progress("saving_result", 0.90)

    save_author_expertise(db, article.id, ae)

    if progress:
        progress("done", 1.0)

    return ae