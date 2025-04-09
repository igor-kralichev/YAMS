from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile

class DealBase(BaseModel):
    name_deal: Optional[str] = Field(None, description="Название сделки")
    seller_id: Optional[int] = Field(None, description="ID аккаунта-продавца")
    seller_price: float = Field(..., gt=0, description="Цена продавца")
    YAMS_percent: Optional[float] = Field(None, description="Процент программы")
    total_cost: Optional[float] = Field(None, description="Финальная стоимость")
    region_id: int = Field(..., description="ID региона сделки")
    address_deal: str = Field(..., description="Адрес сделки (формат: 'Город, улица, дом[, квартира]')")
    date_close: Optional[datetime] = Field(None, description="Дата закрытия сделки")
    photos_url: Optional[List[str]] = Field(default_factory=list, description="Список путей до фотографий сделки")
    deal_type_id: int = Field(..., description="ID типа сделки")
    deal_details_id: Optional[int] = Field(None, description="ID описания сделки")
    deal_branch_id: int = Field(..., description="ID отрасли сделки")


    @validator('photos_url', pre=True, always=True)
    def validate_photos_url(cls, v):
        if isinstance(v, str) and not v:
            return []
        return v

class DealCreate(DealBase):
    # Убираем photos_url из входных данных, так как мы будем принимать файлы через UploadFile
    photos_url: None = None  # Указываем, что это поле не используется при создании

class DealUpdate(BaseModel):
    name_deal: Optional[str] = Field(None, description="Название сделки")
    seller_price: Optional[float] = Field(None, gt=0, description="Цена продавца")
    region_id: Optional[int] = Field(None, description="ID региона сделки")
    address_deal: Optional[str] = Field(None, description="Адрес сделки (например, 'город, улица, дом')")
    photos_url: Optional[List[str]] = Field(default_factory=list, description="Список путей до фотографий сделки")
    deal_details_id: Optional[int] = Field(None, description="ID описания сделки")

class Deal(DealBase):
    id: Optional[int] = Field(default=None, description="Идентификатор сделки")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Дата создания сделки")
    order_count: Optional[int] = None  # Количество покупателей
    feedback_count: Optional[int] = None  # Количество отзывов

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True