# shared/db/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class ChatSchema(BaseModel):
    deal_id: int
    consumer_id: Optional[int]  # ID пользователя, с которым ведётся чат
    name_deal: str
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    participants: Dict[str, str]  # "seller" и "consumer"
    is_purchaser: bool  # Является ли пользователь покупателем

    class Config:
        from_attributes = True