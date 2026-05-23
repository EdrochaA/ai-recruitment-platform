"""
User Entity
Domain model for users with role-based access control
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles with different permission levels"""
    ADMIN = "admin"
    HR = "hr"
    CANDIDATE = "candidate"


class User(BaseModel):
    """User domain model"""
    id: str = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserInDB(User):
    """User stored in database with hashed password"""
    hashed_password: str


class UserCreate(BaseModel):
    """User creation schema - ONLY for candidates (public signup)"""
    name: str
    email: EmailStr
    password: str


class AdminCreateUser(BaseModel):
    """Admin creation of HR/admin users - requires authentication"""
    name: str
    email: EmailStr
    password: str
    role: UserRole  # Admin can specify role (hr or admin)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict
