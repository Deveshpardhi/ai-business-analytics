import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        nullable=False,
        default="completed",
    )

    validation_result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    pii_result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    profile_result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    semantic_result: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    plan_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    analysis_results: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    discovered_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    verified_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    confidence_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    scored_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explained_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ranked_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommended_insights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    dataset_version = relationship(
        "DatasetVersion",
    )