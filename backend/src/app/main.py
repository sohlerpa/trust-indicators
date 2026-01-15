from app.api.router import api_router
from app.core.cors import setup_cors
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI(title="Trust Indicators API", version="0.1.0")

setup_cors(app)

app.include_router(api_router, prefix="/api")
app.mount("/assets", StaticFiles(directory="./assets"), name="assets")
