from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    requests: Mapped[list["AnalysisRequest"]] = relationship(
        "AnalysisRequest",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("customer_id", "id", name="uq_users_customer_user"),
    )

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), nullable=False)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="users")

    requests: Mapped[list["AnalysisRequest"]] = relationship(
        "AnalysisRequest",
        primaryjoin="and_(User.id == foreign(AnalysisRequest.user_id), User.customer_id == foreign(AnalysisRequest.customer_id))",
        viewonly=True,
    )


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    __table_args__ = (
        Index("idx_requests_customer_submitted", "customer_id", "submitted_at"),
        Index("idx_requests_customer_user", "customer_id", "user_id"),
        Index("idx_requests_customer_status", "customer_id", "status"),
        Index("idx_requests_customer_generation", "customer_id", "generation"),
        Index("idx_requests_customer_status_submitted", "customer_id", "status", "submitted_at"),
        Index("idx_requests_customer_user_submitted", "customer_id", "user_id", "submitted_at"),
        CheckConstraint(
            "status IN ('pending', 'success', 'failed')",
            name="ck_analysis_requests_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    generation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estimated_age_low: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_age_high: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="requests",
    )
    photos: Mapped[list["AnalysisPhoto"]] = relationship(
        "AnalysisPhoto",
        back_populates="request",
        cascade="all, delete-orphan",
    )
    probabilities: Mapped[list["AnalysisProbability"]] = relationship(
        "AnalysisProbability",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="AnalysisProbability.generation",
    )


class AnalysisPhoto(Base):
    __tablename__ = "analysis_photos"
    __table_args__ = (
        Index("idx_photos_request", "request_id", "photo_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_requests.id"), nullable=False, index=True
    )
    photo_index: Mapped[int] = mapped_column(Integer, nullable=False)
    photo_ref: Mapped[str] = mapped_column(Text, nullable=False)
    storage_type: Mapped[str] = mapped_column(
        String(20), default="inline", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    request: Mapped["AnalysisRequest"] = relationship(
        "AnalysisRequest",
        back_populates="photos",
    )


class AnalysisProbability(Base):
    __tablename__ = "analysis_probabilities"
    __table_args__ = (
        UniqueConstraint("request_id", "generation", name="uq_request_generation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_requests.id"), nullable=False, index=True
    )
    generation: Mapped[str] = mapped_column(String(20), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)

    request: Mapped["AnalysisRequest"] = relationship(
        "AnalysisRequest",
        back_populates="probabilities",
    )


class StatisticsCache(Base):
    __tablename__ = "statistics_cache"

    customer_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
