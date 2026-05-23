"""
User Entity - Pure Domain Model
No dependencies on frameworks like Pydantic at domain level
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles with different permission levels"""
    ADMIN = "admin"
    HR = "hr"
    CANDIDATE = "candidate"


@dataclass
class User:
    """Pure domain model for User"""
    id: str
    name: str
    email: str
    role: UserRole
    created_at: datetime
    hashed_password: str = ""
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def is_hr(self) -> bool:
        """Check if user is HR"""
        return self.role == UserRole.HR
    
    def is_candidate(self) -> bool:
        """Check if user is candidate"""
        return self.role == UserRole.CANDIDATE
