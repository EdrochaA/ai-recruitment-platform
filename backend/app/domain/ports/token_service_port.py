"""
Token Service Port - Interface for JWT token operations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
from app.domain.entities.user import User


class TokenServicePort(ABC):
    """Abstract interface for token generation and verification"""
    
    @abstractmethod
    def create_token(self, user: User) -> str:
        """Generate a JWT token for a user"""
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token, return payload if valid"""
        pass
    
    @abstractmethod
    def get_payload_from_token(self, token: str) -> Optional[Dict]:
        """Get payload from token without full verification"""
        pass
