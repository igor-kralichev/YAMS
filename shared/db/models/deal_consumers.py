# shared/db/models/deal_consumers.py
from sqlalchemy import Column, Integer, ForeignKey, Table, DateTime, func
from shared.db.base import Base

DealConsumers = Table(
    "deal_consumers",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("deal_id", Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
    Column("consumer_id", Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False
    )
)