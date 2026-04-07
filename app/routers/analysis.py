from __future__ import annotations

from collections import Counter
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db import SessionLocal, get_db
from app.models import AnalysisPhoto, AnalysisRequest, Customer, User
from app.queue import enqueue_analysis_request
from app.schemas import (
    CreateAnalysisRequest,
    RequestDetailResponse,
    RequestStatus,
    RequestSummaryResponse,
    StatisticsResponse,
    UserDetailResponse,
    UserSummaryResponse,
)
from app.worker import process_request

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _process_request_in_background(request_id: str) -> None:
    db = SessionLocal()
    try:
        process_request(db, request_id)
    finally:
        db.close()


def _get_or_create_customer(db: Session, customer_id: str) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        try:
            with db.begin_nested():
                customer = Customer(id=customer_id)
                db.add(customer)
                db.flush()
        except IntegrityError:
            customer = db.get(Customer, customer_id)
            if customer is None:
                raise
    return customer


def _get_or_create_user(db: Session, customer_id: str, user_id: str) -> User:
    stmt = select(User).where(
        and_(
            User.customer_id == customer_id,
            User.id == user_id,
        )
    )
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        try:
            with db.begin_nested():
                user = User(id=user_id, customer_id=customer_id)
                db.add(user)
                db.flush()
        except IntegrityError:
            user = db.execute(stmt).scalar_one()
    return user


@router.post(
    "/{customer_id}/requests",
    response_model=RequestDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis_request(
    customer_id: UUID,
    payload: CreateAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)
    user_id_str = str(payload.user_id)

    _get_or_create_customer(db, customer_id_str)
    _get_or_create_user(db, customer_id_str, user_id_str)

    request_id = str(uuid4())
    request = AnalysisRequest(
        id=request_id,
        customer_id=customer_id_str,
        user_id=user_id_str,
        urgent=payload.urgent,
        status="pending",
    )
    db.add(request)
    db.flush()

    for idx, photo in enumerate(payload.photos):
        db.add(
            AnalysisPhoto(
                request_id=request.id,
                photo_index=idx,
                photo_ref=photo,
                storage_type="inline",
            )
        )

    db.commit()

    enqueued = enqueue_analysis_request(request.id, request.urgent)
    if not enqueued:
        background_tasks.add_task(_process_request_in_background, request.id)

    request = (
        db.query(AnalysisRequest)
        .options(
            joinedload(AnalysisRequest.photos),
            joinedload(AnalysisRequest.probabilities),
        )
        .filter(
            AnalysisRequest.id == request.id,
            AnalysisRequest.customer_id == customer_id_str,
        )
        .one()
    )
    return request


@router.get(
    "/{customer_id}/requests",
    response_model=list[RequestSummaryResponse],
)
def list_analysis_requests(
    customer_id: UUID,
    limit: int = Query(default=100, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    generation: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)

    stmt = select(AnalysisRequest).where(
        AnalysisRequest.customer_id == customer_id_str
    )

    if start is not None:
        stmt = stmt.where(AnalysisRequest.submitted_at >= start)
    if end is not None:
        stmt = stmt.where(AnalysisRequest.submitted_at <= end)
    if user_id is not None:
        stmt = stmt.where(AnalysisRequest.user_id == str(user_id))
    if status_filter is not None:
        stmt = stmt.where(AnalysisRequest.status == status_filter)
    if generation is not None:
        stmt = stmt.where(AnalysisRequest.generation == generation)

    stmt = stmt.order_by(AnalysisRequest.submitted_at.asc()).offset(offset).limit(limit)

    rows = db.execute(stmt).scalars().all()
    return rows


@router.get(
    "/{customer_id}/requests/{request_id}",
    response_model=RequestDetailResponse,
)
def get_analysis_request(
    customer_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)
    request_id_str = str(request_id)

    stmt = (
        select(AnalysisRequest)
        .options(
            joinedload(AnalysisRequest.photos),
            joinedload(AnalysisRequest.probabilities),
        )
        .where(
            and_(
                AnalysisRequest.customer_id == customer_id_str,
                AnalysisRequest.id == request_id_str,
            )
        )
    )

    row = db.execute(stmt).unique().scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return row


@router.get(
    "/{customer_id}/users",
    response_model=list[UserSummaryResponse],
)
def list_users(
    customer_id: UUID,
    limit: int = Query(default=100, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)

    stmt = (
        select(User)
        .where(User.customer_id == customer_id_str)
        .offset(offset)
        .limit(limit)
    )

    users = db.execute(stmt).scalars().all()
    return [{"user_id": user.id} for user in users]


@router.get(
    "/{customer_id}/users/{user_id}",
    response_model=UserDetailResponse,
)
def get_user_detail(
    customer_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)
    user_id_str = str(user_id)

    user_stmt = select(User).where(
        and_(
            User.customer_id == customer_id_str,
            User.id == user_id_str,
        )
    )
    user = db.execute(user_stmt).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    req_stmt = select(AnalysisRequest).where(
        and_(
            AnalysisRequest.customer_id == customer_id_str,
            AnalysisRequest.user_id == user_id_str,
        )
    )
    requests = db.execute(req_stmt).scalars().all()

    return {
        "customer_id": customer_id_str,
        "user_id": user_id_str,
        "requests": requests,
    }


@router.get(
    "/{customer_id}/statistics",
    response_model=StatisticsResponse,
)
def get_statistics(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    customer_id_str = str(customer_id)

    stmt = select(AnalysisRequest).where(
        AnalysisRequest.customer_id == customer_id_str
    )
    rows = db.execute(stmt).scalars().all()

    total = len(rows)
    pending = sum(1 for r in rows if r.status == "pending")
    success = sum(1 for r in rows if r.status == "success")
    failed = sum(1 for r in rows if r.status == "failed")
    urgent = sum(1 for r in rows if r.urgent)

    gen_counter = Counter(r.generation for r in rows if r.generation)

    return {
        "customer_id": customer_id_str,
        "total_requests": total,
        "pending_requests": pending,
        "success_requests": success,
        "failed_requests": failed,
        "urgent_requests": urgent,
        "generation_counts": dict(gen_counter),
    }
