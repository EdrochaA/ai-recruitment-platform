"""
JWT Token Service Implementation
Adapter for token generation and verification using PyJWT
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from app.domain.entities.user import User
from app.domain.ports.token_service_port import TokenServicePort


class JWTTokenService(TokenServicePort):
    """JWT implementation of token service"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_hours: int = 24):
        """Initialize JWT service"""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "name": user.name,
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow(),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_payload_from_token(self, token: str) -> Optional[Dict]:
        """Get payload from token without verification (for debugging)"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception:
            return None
