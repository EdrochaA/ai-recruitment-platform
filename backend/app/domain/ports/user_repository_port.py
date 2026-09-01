"""
User Repository Port
Interface for user persistence operations
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User, UserRole


class UserRepositoryPort(ABC):
    """Abstract interface for user data operations"""
    
    @abstractmethod
    async def create_user(self, name: str, email: str, hashed_password: str, role: UserRole) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        pass

    @abstractmethod
    async def list_users(self, role: Optional[UserRole] = None) -> list[User]:
        """List users, optionally filtered by role"""
        pass
