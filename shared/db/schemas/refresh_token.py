from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RefreshTokenBase(BaseModel):
    token: Optional[str] = Field(None, description="Токен")
    expires_at: Optional[datetime] = Field(None, description="Срок действия токена")

class RefreshTokenCreate(RefreshTokenBase):
    pass

class RefreshToken(RefreshTokenBase):
    id: int
    # Так как теперь привязка идёт через Account, можно убрать user_id и company_id,
    # либо добавить их как опциональные, если логика сохраняется.
    class Config:
        from_attributes = True
