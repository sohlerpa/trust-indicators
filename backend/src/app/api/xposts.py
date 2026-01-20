import uuid

from fastapi import APIRouter, HTTPException, Depends
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.app.api.schemas import XPostOut
from src.app.data.sample_data import X_POSTS
from src.app.service.db_connector import get_db
from src.app.service.progress import set_progress, progress_state, results
from src.app.service.trust.fact_check import run_fact_check_for_text

router = APIRouter()


@router.get("/xposts", response_model=list[XPostOut])
def list_xposts():
    return X_POSTS

@router.post("/xposts/{xpost_id}/fact-check")
def start_fact_check(
    xpost_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    post = next((p for p in X_POSTS if p.id == xpost_id), None)
    if not post:
        raise HTTPException(404)

    run_id = f"xpost:{xpost_id}:{uuid.uuid4().hex[:8]}"

    background.add_task(
        run_and_store_fact_check_for_text,
        run_id=run_id,
        text=post.text,
        db=db,
        x_post_id=xpost_id,
    )

    return {"runId": run_id}


@router.get("/progress/{run_id}")
def get_progress(run_id: str):
    return progress_state.get(
        run_id,
        {"step": "starting", "progress": 0}
    )

@router.get("/fact-check/result/{run_id}")
def get_fact_check_result(run_id: str):
    return results.get(run_id)

def run_and_store_fact_check_for_text(
    *,
    run_id: str,
    text: str,
    db: Session,
    x_post_id: str,
):
    dto = run_fact_check_for_text(
        text=text,
        source_id=run_id,
        db=db,
        x_post_id=x_post_id,
        progress=lambda s, p: set_progress(run_id, s, p),
    )

    results[run_id] = dto