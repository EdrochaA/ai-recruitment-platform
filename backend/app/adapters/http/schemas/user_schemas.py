"""
HTTP Request/Response Schemas - Pydantic Models
Adapter layer for HTTP concerns, not domain logic
"""

from pydantic import BaseModel, EmailStr
from app.domain.entities.user import UserRole


class UserCreateRequest(BaseModel):
    """User signup request schema"""
    name: str
    email: EmailStr
    password: str


class AdminCreateUserRequest(BaseModel):
    """Admin user creation request schema"""
    name: str
    email: EmailStr
    password: str
    role: UserRole


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    name: str
    email: str
    role: str


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
