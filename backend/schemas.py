from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    admin_secret: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_admin: bool
    balance: int
    login_count: int
    request_count: int
    spectral_count: int
    deep_research_count: int
    replenishment_total: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool

class TokenData(BaseModel):
    username: Optional[str] = None

class TempKnowledge(BaseModel):
    content: str
