from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base

class Feedback_Model(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)  # Уже индексирован (PK)
    deal_id = Column(
        Integer,
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=True,
        index=True  # Индекс для JOIN
    )
    stars = Column(Integer, nullable=False)
    details = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False
    )
    author_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True  # Индекс для JOIN
    )
    is_purchaser = Column(Boolean, nullable=False, default=False)

    deal = relationship("Deal_Model", back_populates="feedback", lazy="joined")
    author = relationship("Account_Model", back_populates="feedbacks", lazy="joined")