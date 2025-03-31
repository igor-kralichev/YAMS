from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

import re


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str

    @validator("email")
    def validate_email(cls, value):
        # Проверяем, что email не содержит пробелов
        if " " in value:
            raise ValueError("Email не должен содержать пробелов")
        # Дополнительная проверка: email должен содержать символ "@" и точку после него
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Неверный формат email")
        return value

    @validator("password")
    def validate_password(cls, value):
        # Проверка на минимальную длину
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        # Проверка на наличие хотя бы одной заглавной буквы
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        # Проверка на наличие хотя бы одной строчной буквы
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        # Проверка на наличие хотя бы одной цифры
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        # Проверка на наличие хотя бы одного спецсимвола
        if not re.search(r"[!@#$%^&*()_+{}\[\]:;<>,.?/~`\\|-]", value):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return value


class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    role: str

    class Config:
        from_attributes = True
