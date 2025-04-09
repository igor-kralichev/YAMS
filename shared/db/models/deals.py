from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.db.base import Base
from shared.db.models import deal_consumers

class Deal_Model(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    name_deal = Column(String(255), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    seller_price = Column(Numeric(12,2), nullable=False)
    YAMS_percent = Column(Numeric(12,2), nullable=True)
    total_cost = Column(Numeric(12,2), nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)
    address_deal = Column(String(255), nullable=False)
    date_close = Column(
        DateTime(timezone=True),
        nullable=True
    )
    photos_url = Column(ARRAY(String), nullable=True)
    deal_details_id = Column(Integer, ForeignKey("deal_details.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False
    )
    deal_branch_id = Column(Integer, ForeignKey("deal_branch.id", ondelete="SET NULL"), nullable=True)
    deal_type_id = Column(Integer, ForeignKey("deal_type.id", ondelete="SET NULL"), nullable=True)

    # Связи
    region = relationship("Region", back_populates="deals")
    deal_details = relationship("DealDetail", back_populates="deals")
    deal_branch = relationship("DealBranch", back_populates="deals")
    feedback = relationship("Feedback_Model", back_populates="deal", passive_deletes=True)
    messages = relationship("Message_Model", back_populates="deal", cascade="all, delete-orphan")
    consumers = relationship(
        "Account_Model",
        secondary="deal_consumers",  # Указываем имя таблицы как строку
        back_populates="purchased_deals",
        order_by="deal_consumers.c.created_at"
    )
    seller = relationship("Account_Model", foreign_keys=[seller_id])
    deal_type = relationship("DealTypes", back_populates="deals")