from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base

class Message_Model(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(
        Integer,
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    consumer_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    sender_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    recipient_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.timezone('Europe/Moscow', func.now()),
        nullable=False,
        index=True
    )

    deal = relationship("Deal_Model", back_populates="messages")
    sender = relationship("Account_Model", foreign_keys=[sender_id])
    recipient = relationship("Account_Model", foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            "id": self.id,
            "deal_id": self.deal_id,
            "consumer_id": self.consumer_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }