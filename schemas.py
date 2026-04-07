from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RequestStatus = Literal["pending", "success", "failed"]


class CreateAnalysisRequest(BaseModel):
    user_id: UUID
    urgent: bool = False
    photos: list[str] = Field(default_factory=list, min_length=1)


class RequestPhotoResponse(BaseModel):
    photo_index: int
    photo_ref: str
    storage_type: str

    model_config = ConfigDict(from_attributes=True)


class ProbabilityResponse(BaseModel):
    generation: str
    probability: float

    model_config = ConfigDict(from_attributes=True)


class RequestSummaryResponse(BaseModel):
    id: UUID
    customer_id: UUID
    user_id: UUID
    urgent: bool
    status: RequestStatus
    submitted_at: datetime
    completed_at: datetime | None = None
    generation: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RequestDetailResponse(BaseModel):
    id: UUID
    customer_id: UUID
    user_id: UUID
    urgent: bool
    status: RequestStatus
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    generation: str | None = None
    estimated_age_low: int | None = None
    estimated_age_high: int | None = None
    error_message: str | None = None
    engine_version: str | None = None
    photos: list[RequestPhotoResponse] = Field(default_factory=list)
    probabilities: list[ProbabilityResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserSummaryResponse(BaseModel):
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    customer_id: UUID
    user_id: UUID
    requests: list[RequestSummaryResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class StatisticsResponse(BaseModel):
    customer_id: UUID
    total_requests: int
    pending_requests: int
    success_requests: int
    failed_requests: int
    urgent_requests: int
    generation_counts: dict[str, int] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str