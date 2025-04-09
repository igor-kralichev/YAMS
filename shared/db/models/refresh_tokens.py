from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), nullable=True)           # Токен
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Срок действия
    # ondelete CASCADE – если аккаунт удалён, токены удаляются
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)

    # Связи
    account = relationship("Account_Model", back_populates="refresh_tokens")
