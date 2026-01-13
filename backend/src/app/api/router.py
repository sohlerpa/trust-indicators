from fastapi import APIRouter
from app.api.feed import router as feed_router
from app.api.articles import router as articles_router
from app.api.xposts import router as xposts_router
from app.api.source_funding import router as source_funding_router

api_router = APIRouter()
api_router.include_router(feed_router, tags=["feed"])
api_router.include_router(articles_router, tags=["articles"])
api_router.include_router(xposts_router, tags=["xposts"])
api_router.include_router(source_funding_router, tags=["sources"])