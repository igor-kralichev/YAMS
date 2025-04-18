from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import date

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

    class Config:
        from_attributes = True