from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.service.db_connector import get_db
from src.modules.source_funding.queries import GET_DOMAIN_OWNERS, GET_FEED_OWNERSHIP

router = APIRouter()

@router.get("/domain/{domain}/owners")
def get_domain_owners(domain: str, db: Session = Depends(get_db)):
    result = db.execute(GET_DOMAIN_OWNERS, {"domain": domain}).fetchall()
    return [
        {"owner": row.name, "percent": float(row.ownership_percent)}
        for row in result
    ]

@router.post("/feed/diversity")
def feed_diversity(domains: List[str], db: Session = Depends(get_db)):
    result = db.execute(GET_FEED_OWNERSHIP, {"domains": domains}).fetchall()
    return [
        {"owner": row.owner_name, "influence": float(row.total_influence)}
        for row in result
    ]