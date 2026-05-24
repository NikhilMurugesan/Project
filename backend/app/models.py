# SQLAlchemy models. Three tables: scenarios, trucks, orders. A scenario
# is just a named container so we can have multiple demos sitting in the
# same SQLite file without them stepping on each other.
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trucks: Mapped[list["Truck"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"))
    name: Mapped[str] = mapped_column(String(60))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    capacity_kg: Mapped[float] = mapped_column(Float)
    # JSON list of capability strings (e.g. ["refrigerated", "hazmat"]).
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    # All time fields are minutes since 00:00. Easier to reason about than
    # datetimes when we don't care about dates or timezones.
    shift_start: Mapped[int] = mapped_column(Integer, default=8 * 60)
    shift_end: Mapped[int] = mapped_column(Integer, default=18 * 60)
    avg_speed_kmh: Mapped[float] = mapped_column(Float, default=40.0)
    cost_per_km: Mapped[float] = mapped_column(Float, default=1.0)

    scenario: Mapped[Scenario] = relationship(back_populates="trucks")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"))
    code: Mapped[str] = mapped_column(String(60))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    required_capabilities: Mapped[list] = mapped_column(JSON, default=list)
    # Time window the customer is willing to accept delivery in, again as
    # minutes since 00:00.
    tw_start: Mapped[int] = mapped_column(Integer)
    tw_end: Mapped[int] = mapped_column(Integer)
    service_minutes: Mapped[int] = mapped_column(Integer, default=10)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1 = whenever, 5 = drop everything
    sla_deadline: Mapped[int] = mapped_column(Integer)  # must be served by this minute

    scenario: Mapped[Scenario] = relationship(back_populates="orders")
