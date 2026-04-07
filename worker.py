from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AnalysisProbability, AnalysisRequest
from app.services.engine import EngineError, run_engine


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def process_request(db: Session, request_id: str) -> None:
    stmt = (
        select(AnalysisRequest)
        .options(
            joinedload(AnalysisRequest.photos),
            joinedload(AnalysisRequest.probabilities),
        )
        .where(AnalysisRequest.id == request_id)
    )
    request = db.execute(stmt).unique().scalar_one_or_none()
    if request is None:
        return

    try:
        print(f"[worker] start processing request={request_id}")

        request.started_at = utcnow()
        db.commit()
        db.refresh(request)

        content = [
            photo.photo_ref
            for photo in sorted(request.photos, key=lambda p: p.photo_index)
        ]

        result = run_engine(request.id, content)

        results = result.get("results", {})
        generations = results.get("generations", {})
        primary_generation = results.get("primary_generation")
        age = results.get("age")

        if not primary_generation:
            raise EngineError("Engine output missing primary_generation")

        if not isinstance(generations, dict):
            raise EngineError("Engine output missing valid generations")

        request.status = "success"
        request.generation = primary_generation
        request.completed_at = utcnow()
        request.error_message = None
        request.engine_version = "v1.0.0"

        if isinstance(age, int):
            request.estimated_age_low = age
            request.estimated_age_high = age
        else:
            request.estimated_age_low = None
            request.estimated_age_high = None

        request.probabilities.clear()

        for name, value in generations.items():
            request.probabilities.append(
                AnalysisProbability(
                    generation=name,
                    probability=float(value),
                )
            )

        db.commit()
        print(f"[worker] request={request_id} success")

    except EngineError as exc:
        request.status = "failed"
        request.generation = None
        request.estimated_age_low = None
        request.estimated_age_high = None
        request.error_message = str(exc)
        request.completed_at = utcnow()
        request.probabilities.clear()
        db.commit()
        print(f"[worker] request={request_id} failed: {exc}")

    except Exception as exc:
        request.status = "failed"
        request.generation = None
        request.estimated_age_low = None
        request.estimated_age_high = None
        request.error_message = f"Unexpected error: {exc}"
        request.completed_at = utcnow()
        request.probabilities.clear()
        db.commit()
        print(f"[worker] request={request_id} unexpected failure: {exc}")