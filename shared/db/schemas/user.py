from pydantic import BaseModel, EmailStr, Field, validator, computed_field
from datetime import datetime
from typing import Optional
import re
from .account import AccountCreate, Account

class UserBase(BaseModel):
    fullname: str = Field(..., description="ФИО пользователя")
    photo_url: Optional[str] = Field(None, description="Путь до фото")

class UserCreate(UserBase):
    account: AccountCreate = Field(..., description="Данные для создания аккаунта пользователя")

class User(BaseModel):
    id: int
    fullname: str
    account_id: int
    account: Account

class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_num: Optional[int] = None
    region_id: Optional[int] = None

    @validator('phone_num')
    def validate_phone(cls, v):
        if v and len(str(v)) != 11:
            raise ValueError('Номер должен содержать 11 цифр')
        return v

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True