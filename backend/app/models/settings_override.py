"""Persistent settings overrides (single-row table)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SettingsOverride(Base):
    __tablename__ = "settings_overrides"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="global")
    overrides_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<SettingsOverride updated_at={self.updated_at}>"
