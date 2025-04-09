import re
from typing import Optional
from pydantic import BaseModel, Field, computed_field, EmailStr, validator
from datetime import date, datetime
from .account import Account, AccountCreate  # Импорт схемы Account

class CompanyBase(BaseModel):
    name: str = Field(..., description="Название компании")
    description: Optional[str] = Field(None, description="Описание компании")
    slogan: Optional[str] = Field(None, description="Слоган")
    address: Optional[str] = Field(None, description="Адрес")
    logo_url: Optional[str] = Field(None, description="Путь до логотипа")
    employees: Optional[int] = Field(None, description="Количество сотрудников")
    year_founded: Optional[date] = Field(None, description="Год основания")
    website: Optional[str] = Field(None, description="Ссылка на сайт")

class CompanyCreate(CompanyBase):
    account: AccountCreate = Field(..., description="Данные аккаунта компании")

class CompanyUpdate(BaseModel):
    # Поля компании
    name: Optional[str] = None
    description: Optional[str] = None
    slogan: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    employees: Optional[int] = None
    year_founded: Optional[date] = None
    website: Optional[str] = None

    # Поля аккаунта
    email: Optional[EmailStr] = None
    phone_num: Optional[int] = None
    region_id: Optional[int] = None

    @validator('phone_num')
    def validate_phone(cls, v):
        if v and len(str(v)) != 11:
            raise ValueError('Номер должен содержать 11 цифр')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Неверный формат email')
        return v

class Company(CompanyBase):
    id: int
    account_id: int
    account: Account  # Прямая ссылка на связанный аккаунт

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Для работы с ORM-объектами