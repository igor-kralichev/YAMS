# shared/db/schemas/company.py
import re
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator, computed_field
from datetime import date
from .account import Account, AccountCreate

class CompanyBase(BaseModel):
    name: str = Field(..., description="Название компании")
    description: Optional[str] = Field(None, description="Описание компании")
    slogan: Optional[str] = Field(None, description="Слоган")
    legal_address: Optional[str] = Field(None, description="Юридический адрес")
    actual_address: Optional[str] = Field(None, description="Фактический адрес")
    logo_url: Optional[str] = Field(None, description="Путь до логотипа")
    employees: Optional[int] = Field(None, description="Количество сотрудников")
    year_founded: Optional[date] = Field(None, description="Год основания")
    website: Optional[str] = Field(None, description="Ссылка на сайт")
    inn: Optional[str] = Field(None, description="ИНН (10 цифр)")
    kpp: Optional[str] = Field(None, description="КПП (9 цифр)")
    ogrn: Optional[str] = Field(None, description="ОГРН (13 цифр)")
    oktmo: Optional[str] = Field(None, description="ОКТМО (8 или 11 цифр)")
    okpo: Optional[str] = Field(None, description="ОКПО (8 цифр)")
    director_full_name: Optional[str] = Field(None, description="ФИО директора")
    social_media_links: Optional[List[str]] = Field(None, description="Ссылки на соцсети")
    partner_companies: Optional[List[int]] = Field(None, description="ID партнёрских компаний (до 3)")

    @validator('inn')
    def validate_inn(cls, v):
        if v and (not v.isdigit() or len(v) != 10):
            raise ValueError('ИНН должен содержать ровно 10 цифр')
        return v

    @validator('kpp')
    def validate_kpp(cls, v):
        if v and (not v.isdigit() or len(v) != 9):
            raise ValueError('КПП должен содержать ровно 9 цифр')
        return v

    @validator('ogrn')
    def validate_ogrn(cls, v):
        if v and (not v.isdigit() or len(v) != 13):
            raise ValueError('ОГРН должен содержать ровно 13 цифр')
        return v

    @validator('oktmo')
    def validate_oktmo(cls, v):
        if v and (not v.isdigit() or len(v) not in [8, 11]):
            raise ValueError('ОКТМО должен содержать 8 или 11 цифр')
        return v

    @validator('okpo')
    def validate_okpo(cls, v):
        if v and (not v.isdigit() or len(v) != 8):
            raise ValueError('ОКПО должен содержать ровно 8 цифр')
        return v

    @validator('social_media_links', each_item=True)
    def validate_social_media_links(cls, v):
        social_media_patterns = [
            # Разрешаем только vk.com, ok.ru и t.me
            r'^https?://(www\.)?(vk\.com|ok\.ru)/.+$',
            r'^https?://(t\.me|telegram\.me)/[a-zA-Z0-9_]+$'  # Для Telegram
        ]

        if v and not any(re.match(pattern, v) for pattern in social_media_patterns):
            raise ValueError(f'Разрешены только ссылки на VK, OK и Telegram. Недопустимая ссылка: {v}')
        return v

    @validator('partner_companies')
    def validate_partner_companies(cls, v):
        if v and len(v) > 3:
            raise ValueError('Можно указать не более 3 партнёрских компаний')
        return v

    @validator('director_full_name')
    def validate_director_full_name(cls, v):
        if v and not re.match(r'^[А-ЯЁа-яё\s-]{2,}\s[А-ЯЁа-яё\s-]{2,}(\s[А-ЯЁа-яё\s-]{2,})?$', v):
            raise ValueError('ФИО директора должно содержать минимум имя и фамилию на кириллице')
        return v

class CompanyCreate(CompanyBase):
    account: AccountCreate = Field(..., description="Данные аккаунта компании")

class CompanyUpdate(CompanyBase):
    # Поля компании
    name: Optional[str] = None
    description: Optional[str] = None
    slogan: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    logo_url: Optional[str] = None
    employees: Optional[int] = None
    year_founded: Optional[date] = None
    website: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    oktmo: Optional[str] = None
    okpo: Optional[str] = None
    director_full_name: Optional[str] = None
    social_media_links: Optional[List[str]] = None
    partner_companies: Optional[List[int]] = None

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

    @computed_field
    @property
    def partner_companies_names(self) -> List[dict]:
        # Это поле будет заполняться в роуте, здесь заглушка
        return []

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True