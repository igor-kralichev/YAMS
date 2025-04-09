from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base

class Feedback_Model(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(
        Integer,
        ForeignKey("deals.id", ondelete="CASCADE"),  # Изменили на CASCADE, чтобы отзывы удалялись
        nullable=True
    )
    stars = Column(Integer, nullable=False)  # Оценка (от 0 до 5)
    details = Column(Text, nullable=False)  # Описание отзыва
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False
    )  # Время создания отзыва
    author_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),  # Устанавливаем NULL при удалении аккаунта
        nullable=True
    )
    is_purchaser = Column(Boolean, nullable=False, default=False)  # Метка: покупал ли пользователь сделку

    deal = relationship("Deal_Model", back_populates="feedback", lazy="joined")
    author = relationship("Account_Model", back_populates="feedbacks", lazy="joined")