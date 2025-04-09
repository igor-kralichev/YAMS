from sqlalchemy import Column, Integer, String, Boolean, DateTime, BIGINT, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.base import Base
from .deal_consumers import DealConsumers

class Account_Model(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    is_verified = Column(Boolean, nullable=False)
    verification_token = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False
    )
    role = Column(String(255), nullable=False)
    phone_num = Column(BIGINT, nullable=True)
    # ondelete SET NULL – значит, если удалят регион, поле станет NULL
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)

    # Связи
    user = relationship("User_Model", back_populates="account", uselist=False, lazy="joined")
    company = relationship("Company_Model", back_populates="account", uselist=False, lazy="joined")
    refresh_tokens = relationship("RefreshToken", back_populates="account", cascade="all, delete-orphan")
    region = relationship("Region", back_populates="accounts")
    feedbacks = relationship("Feedback_Model", back_populates="author", passive_deletes=True)
    purchased_deals = relationship(
        "Deal_Model",
        secondary="deal_consumers",
        back_populates="consumers"
    )