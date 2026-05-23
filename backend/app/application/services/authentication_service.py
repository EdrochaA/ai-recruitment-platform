"""
Authentication Services - Application Layer
Coordinates authentication use cases
"""

from app.domain.entities.user import User, UserRole
from app.domain.ports.user_repository_port import UserRepositoryPort
from app.domain.ports.password_hasher_port import PasswordHasherPort
from app.domain.ports.token_service_port import TokenServicePort


class AuthenticationService:
    """High-level authentication service - Coordinates use cases"""
    
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort
    ):
        """Initialize authentication service with dependencies"""
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
    
    async def register_user(self, name: str, email: str, password: str) -> dict:
        """Register a new CANDIDATE user (public signup)"""
        # Check if user already exists
        if await self.user_repository.user_exists(email):
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        hashed_password = self.password_hasher.hash_password(password)
        
        # Create user as CANDIDATE (always for public signup)
        user = await self.user_repository.create_user(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role=UserRole.CANDIDATE
        )
        
        # Generate token
        token = self.token_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            }
        }
    
    async def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate user and return token"""
        # Get user by email
        user = await self.user_repository.get_user_by_email(email)
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self.password_hasher.verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        # Generate token
        token = self.token_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            }
        }
    
    async def create_user_as_admin(
        self,
        admin_email: str,
        name: str,
        email: str,
        password: str,
        role: str
    ) -> dict:
        """Create a new HR/ADMIN user (admin only)"""
        # Verify admin is actually admin
        admin_user = await self.user_repository.get_user_by_email(admin_email)
        if not admin_user or not admin_user.is_admin():
            raise ValueError("Only admins can create users")
        
        # Check if user already exists
        if await self.user_repository.user_exists(email):
            raise ValueError(f"User with email {email} already exists")
        
        # Validate role
        if role not in ["hr", "admin"]:
            raise ValueError("Role must be 'hr' or 'admin'")
        
        # Hash password
        hashed_password = self.password_hasher.hash_password(password)
        
        # Create user with specified role
        user = await self.user_repository.create_user(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role=UserRole(role)
        )
        
        # Generate token
        token = self.token_service.create_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            }
        }
