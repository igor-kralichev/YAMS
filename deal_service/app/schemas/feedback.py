from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional

class FeedbackBase(BaseModel):
    deal_id: Optional[int] = Field(None, description="ID сделки")
    stars: int = Field(..., description="Оценка (от 0 до 5)")
    details: str = Field(..., description="Описание отзыва")

    @validator("stars")
    def validate_stars(cls, value):
        if not 0 <= value <= 5:
            raise ValueError("Оценка должна быть от 0 до 5")
        return value

class FeedbackCreate(BaseModel):
    stars: int = Field(..., description="Оценка (от 0 до 5)")
    details: str = Field(..., description="Описание отзыва")

    @validator("stars")
    def validate_stars(cls, value):
        if not 0 <= value <= 5:
            raise ValueError("Оценка должна быть от 0 до 5")
        return value

class Feedback(FeedbackBase):
    id: int
    author_id: Optional[int] = Field(None, description="ID автора (NULL если аккаунт удалён)")  # Добавлено поле
    created_at: datetime
    is_purchaser: bool = False

    class Config:
        from_attributes = True