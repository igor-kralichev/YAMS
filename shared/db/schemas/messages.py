from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    sender_id: int = Field(..., description="ID аккаунта отправителя")
    recipient_id: int = Field(..., description="ID аккаунта получателя")
    content: str = Field(..., description="Текст сообщения")
    deal_id: int = Field(..., description="ID сделки")

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    created_at: datetime


    class Config:
        from_attributes = True
