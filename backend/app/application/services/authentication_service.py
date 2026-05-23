"""
Authentication Services
Handles password hashing, JWT token generation, and verification
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from app.domain.entities.user import UserInDB


class PasswordService:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class JWTService:
    """JWT token generation and verification"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_hours: int = 24):
        """Initialize JWT service"""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user: UserInDB) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "name": user.name,
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow(),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
    
    def get_payload_from_token(self, token: str) -> Optional[dict]:
        """Get payload from token without verification (for debugging)"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception:
            return None


class AuthenticationService:
    """High-level authentication service"""
    
    def __init__(self, user_repository, jwt_service: JWTService):
        """Initialize authentication service"""
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.password_service = PasswordService()
    
    async def register_user(self, name: str, email: str, password: str) -> dict:
        """Register a new CANDIDATE user (public signup)"""
        from app.domain.entities.user import UserCreate, UserRole
        
        # Check if user already exists
        if await self.user_repository.user_exists(email):
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        hashed_password = self.password_service.hash_password(password)
        
        # Create user as CANDIDATE (always)
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
        )
        
        user = await self.user_repository.create_user(
            user_data, 
            hashed_password,
            role=UserRole.CANDIDATE.value
        )
        
        # Generate token
        token = self.jwt_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            }
        }
    
    async def create_user_as_admin(self, admin_email: str, name: str, email: str, password: str, role: str) -> dict:
        """Create a new HR/ADMIN user (admin only)"""
        from app.domain.entities.user import UserCreate, UserRole
        
        # Verify admin is actually admin
        admin_user = await self.user_repository.get_user_by_email(admin_email)
        if not admin_user or admin_user.role != UserRole.ADMIN:
            raise ValueError("Only admins can create users")
        
        # Check if user already exists
        if await self.user_repository.user_exists(email):
            raise ValueError(f"User with email {email} already exists")
        
        # Validate role
        if role not in ["hr", "admin"]:
            raise ValueError("Role must be 'hr' or 'admin'")
        
        # Hash password
        hashed_password = self.password_service.hash_password(password)
        
        # Create user with specified role
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
        )
        
        user = await self.user_repository.create_user(
            user_data, 
            hashed_password, 
            role=role
        )
        
        # Generate token
        token = self.jwt_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": role,
            }
        }
    
    async def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate user and return token"""
        # Get user by email
        user = await self.user_repository.get_user_by_email(email)
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self.password_service.verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        # Generate token
        token = self.jwt_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            }
        }
