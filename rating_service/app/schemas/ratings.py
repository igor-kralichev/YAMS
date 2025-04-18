from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import date, datetime

class IndustrySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class PartnerSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CompanyShortSchema(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    description: Optional[str]
    director_full_name: Optional[str]
    average_rating: Optional[float]  # Средняя оценка
    industries: List[IndustrySchema]  # Индустрии сделок
    partners: List[PartnerSchema]  # Названия партнёров
    is_top: bool = Field(..., description="Флаг топ-позиции")

    class Config:
        from_attributes = True

class CompanyDetailSchema(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    slogan: Optional[str]
    description: Optional[str]
    legal_address: Optional[str]
    actual_address: Optional[str]
    employees: Optional[int]
    year_founded: Optional[date]
    website: Optional[HttpUrl]
    inn: Optional[str]
    social_media_links: Optional[List[HttpUrl]]
    partners: List[PartnerSchema]

    class Config:
        from_attributes = True

class CompanyVikorSchema(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    average_rating: Optional[float]
    feedback_count: int
    order_count: int
    repeat_customer_orders: int
    vikor_score: float  # Вычисленный рейтинг по VIKOR
    is_top: bool = Field(..., description="Флаг топ-позиции")

    class Config:
        from_attributes = True

class BuyingTopBase(BaseModel):
    """Базовая схема для покупки топ-позиции"""
    id_company: int = Field(..., description="ID компании")
    days: int = Field(..., description="Количество суток для топ-позиции")

class BuyingTopCreate(BuyingTopBase):
    """Схема для создания записи"""
    pass

class BuyingTopUpdate(BaseModel):
    """Схема для обновления записи"""
    time_stop: Optional[datetime] = Field(None, description="Новое время окончания")
    total_spent: Optional[float] = Field(None, description="Общая сумма потраченных денег")
    purchase_count: Optional[int] = Field(None, description="Количество покупок")

class BuyingTopInDB(BuyingTopBase):
    """Схема для записи в БД"""
    id: int = Field(..., description="ID записи")
    time_stop: datetime = Field(..., description="Время окончания топ-позиции")
    total_spent: float = Field(..., description="Общая сумма потраченных денег")
    purchase_count: int = Field(..., description="Количество покупок")
    created_at: datetime = Field(..., description="Время создания")

    class Config:
        from_attributes = True

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