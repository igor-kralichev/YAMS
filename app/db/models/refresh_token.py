from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Связь с пользователем
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # Связь с компанией
    expires_at = Column(DateTime)
    user = relationship("User", back_populates="refresh_tokens")
    company = relationship("Company", back_populates="refresh_tokens")