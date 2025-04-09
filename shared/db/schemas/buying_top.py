from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class BuyingTopBase(BaseModel):
    """Базовая схема для покупки топ-позиции"""
    id_company: int = Field(..., description="ID компании")
    time_stop: datetime = Field(..., description="Время окончания топ-позиции")

class BuyingTopCreate(BuyingTopBase):
    """Схема для создания записи"""
    pass

class BuyingTopUpdate(BaseModel):
    """Схема для обновления записи"""
    time_stop: Optional[datetime] = Field(None, description="Новое время окончания")

class BuyingTopInDB(BuyingTopBase):
    """Схема для записи в БД"""
    id: int = Field(..., description="ID записи")
    created_at: datetime = Field(..., description="Время создания")

    class Config:
        from_attributes = True  # Для совместимости с SQLAlchemy (ранее orm_mode)

class BuyingTopPublic(BuyingTopInDB):
    """Схема для публичного ответа API"""
    company_name: Optional[str] = Field(None, description="Название компании")

    @classmethod
    def from_orm_with_company(cls, db_obj, company_name: str):
        """Дополнительный метод для подтягивания названия компании"""
        return cls(
            **db_obj.__dict__,
            company_name=company_name
        )