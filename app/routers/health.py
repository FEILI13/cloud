from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "database": database_status,
        "timestamp": datetime.now(timezone.utc),
    }