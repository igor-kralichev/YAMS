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
    average_rating: Optional[float]
    region_id: int
    region_name: str
    industries: List[IndustrySchema]
    partners: List[PartnerSchema]
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
    region_id: Optional[int]
    region_name: Optional[str]
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
    region_id: int
    region_name: str
    is_top: bool = Field(..., description="Флаг топ-позиции")

    class Config:
        from_attributes = True

class BuyingTopBase(BaseModel):
    """Схема для запроса (поле days передается в запросе, но не хранится в БД)"""
    id_company: int = Field(..., description="ID компании")
    days: int = Field(..., ge=1, description="Количество суток для топ-позиции")

class BuyingTopCreate(BuyingTopBase):  # <--- Этот класс должен быть объявлен
    """Схема для создания записи"""
    pass

class BuyingTopInDB(BaseModel):
    id: int = Field(..., description="ID записи")
    id_company: int = Field(..., description="ID компании")
    time_stop: datetime = Field(..., description="Время окончания топ-позиции")
    total_spent: float = Field(..., description="Общая сумма потраченных денег")
    purchase_count: int = Field(..., description="Количество покупок")

    class Config:
        from_attributes = True

class BuyingTopPublic(BuyingTopInDB):
    company_name: Optional[str] = Field(None, description="Название компании")

    @classmethod
    def from_orm_with_company(cls, db_obj, company_name: str):
        return cls(
            id=db_obj.id,
            id_company=db_obj.id_company,
            time_stop=db_obj.time_stop,
            total_spent=float(db_obj.total_spent),
            purchase_count=db_obj.purchase_count,
            company_name=company_name
        )