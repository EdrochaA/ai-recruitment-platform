"""
User Repository Port
Interface for user persistence operations
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import UserInDB, UserCreate


class UserRepositoryPort(ABC):
    """Abstract interface for user data operations"""
    
    @abstractmethod
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> UserInDB:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        pass
