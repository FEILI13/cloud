from __future__ import annotations

from fastapi import FastAPI

from .db import Base, engine
from .routers.analysis import router as analysis_router
from .routers.health import router as health_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgeOverflow GCAS",
    version="0.1.0",
)

app.include_router(analysis_router)
app.include_router(health_router)