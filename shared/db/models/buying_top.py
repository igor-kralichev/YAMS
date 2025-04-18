from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.base import Base

class BuyTop(Base):
    __tablename__ = "buy_top"

    id = Column(Integer, primary_key=True, index=True)
    id_company = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    time_stop = Column(DateTime(timezone=True), nullable=True)
    total_spent = Column(Numeric(12, 2), nullable=False, default=0.00)  # Общая сумма потраченных денег
    purchase_count = Column(Integer, nullable=False, default=0)  # Количество покупок топа

    # Связи
    company = relationship("Company_Model", back_populates="top_purchases")