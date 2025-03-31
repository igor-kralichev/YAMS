from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Подтверждение email
    verification_token = Column(String, nullable=True)  # Токен для подтверждения
    created_at = Column(DateTime, server_default=func.now())
    role = Column(String, default="user")  # Роль для проверки прав
    refresh_tokens = relationship("RefreshToken", back_populates="user")