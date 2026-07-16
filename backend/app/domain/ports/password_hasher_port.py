"""
Password Hasher Port - Interface for password hashing operations
"""

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """Abstract interface for password hashing"""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plaintext password"""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hash"""
        pass
