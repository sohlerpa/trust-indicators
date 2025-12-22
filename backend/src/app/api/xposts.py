from fastapi import APIRouter
from app.api.schemas import XPost
from app.data.sample_data import X_POSTS

router = APIRouter()


@router.get("/xposts", response_model=list[XPost])
def list_xposts():
    return X_POSTS
