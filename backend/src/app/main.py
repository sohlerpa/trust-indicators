from fastapi import FastAPI
from app.core.cors import setup_cors
from app.api.router import api_router

app = FastAPI(title="Trust Indicators API", version="0.1.0")

setup_cors(app)

app.include_router(api_router, prefix="/api")
