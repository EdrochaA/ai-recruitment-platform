"""
Bcrypt Password Hasher Implementation
Adapter for password hashing using bcrypt library
"""

import bcrypt
from app.domain.ports.password_hasher_port import PasswordHasherPort


class BcryptPasswordHasher(PasswordHasherPort):
    """Bcrypt implementation of password hasher"""
    
    def __init__(self, rounds: int = 12):
        """Initialize with bcrypt rounds (security parameter)"""
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
