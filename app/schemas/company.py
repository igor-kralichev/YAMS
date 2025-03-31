from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import re

class CompanyBase(BaseModel):
    email: EmailStr
    name: str

class CompanyCreate(CompanyBase):
    password: str

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

class Company(CompanyBase):
    id: int
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True