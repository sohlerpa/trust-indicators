from fastapi import FastAPI
from modules.source_funding.endpoints import funding_router

app = FastAPI()
app.include_router(funding_router)
