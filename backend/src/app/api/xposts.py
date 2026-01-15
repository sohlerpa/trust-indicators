from fastapi import APIRouter

from src.app.api.schemas import XPostOut
from src.app.data.sample_data import X_POSTS

router = APIRouter()


@router.get("/xposts", response_model=list[XPostOut])
def list_xposts():
    return X_POSTS
