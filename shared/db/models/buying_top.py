from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.base import Base

class BuyTop(Base):
    __tablename__ = "buy_top"

    id = Column(Integer, primary_key=True, index=True)
    # ondelete CASCADE – если компания удаляется, связанные записи удаляются
    id_company = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    time_stop = Column(DateTime(timezone=True), nullable=True)

    # Связи
    company = relationship("Company_Model", back_populates="top_purchases")
