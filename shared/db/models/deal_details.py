from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from shared.db.base import Base

class DealDetail(Base):
    __tablename__ = "deal_details"

    id = Column(Integer, primary_key=True, index=True)
    detail = Column(String(255), nullable=False)  # Пояснение к состоянию сделки

    # Связи: связь со сделкой осуществляется через поле deal_details_id в сделках
    deals = relationship("Deal_Model", back_populates="deal_details")
