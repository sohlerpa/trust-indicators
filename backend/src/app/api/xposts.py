from fastapi import APIRouter
from fastapi import HTTPException

from src.app.service.db_connector import get_db
from src.app.service.trust.fact_check import run_fact_check, run_fact_check_for_text
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends


from src.app.api.schemas import XPostOut
from src.app.data.sample_data import X_POSTS

router = APIRouter()


@router.get("/xposts", response_model=list[XPostOut])
def list_xposts():
    return X_POSTS

@router.get("/xposts/{xpost_id}/fact-check")
def fact_check_xpost(xpost_id: str, db: Session = Depends(get_db)):
    post = next((p for p in X_POSTS if p.id == xpost_id), None)

    if not post:
        raise HTTPException(404, "X post not found")

    return run_fact_check_for_text(
        text=post.text,
        source_id=f"xpost:{post.id}",
        db=db,
    )