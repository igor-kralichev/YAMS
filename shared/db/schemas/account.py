from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
import re

class AccountBase(BaseModel):
    email: EmailStr = Field(..., description="Email для авторизации")
    phone_num: Optional[int] = Field(None, description="Телефон (11 цифр, если указан)")
    region_id: Optional[int] = Field(None, description="ID региона")

class AccountCreate(AccountBase):
    password: str = Field(..., description="Пароль для аккаунта")

    @validator("email")
    def validate_email(cls, value):
        if " " in value:
            raise ValueError("Email не должен содержать пробелов")
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Неверный формат email")
        return value

    @validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*()_+{}\[\]:;<>,.?/~`\\|-]", value):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return value

class Account(AccountBase):
    id: int
    is_active: bool
    is_verified: bool
    verification_token: Optional[str] = Field(None, description="Токен верификации")
    created_at: datetime
    role: str
    purchased_deal_ids: List[int] = Field(default_factory=list, description="Список ID купленных сделок")  # Добавляем

    class Config:
        from_attributes = True
