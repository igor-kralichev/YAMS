from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from shared.db.base import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Название региона

    # Связи
    deals = relationship("Deal_Model", back_populates="region")
    accounts = relationship("Account_Model", back_populates="region")
