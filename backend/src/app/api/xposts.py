from fastapi import APIRouter
from fastapi import HTTPException
from src.app.service.trust.fact_check import run_fact_check

from src.app.api.schemas import XPostOut
from src.app.data.sample_data import X_POSTS

router = APIRouter()


@router.get("/xposts", response_model=list[XPostOut])
def list_xposts():
    return X_POSTS

@router.get("/xposts/{id}/fact-check")
def fact_check_xpost(id: str):
    post = next((p for p in X_POSTS if p.id == id), None)

    if not post:
        raise HTTPException(404, "X post not found")

    return None # run_fact_check(post.text) TODO