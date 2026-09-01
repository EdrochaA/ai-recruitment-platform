"""
Authentication Router
HTTP endpoints for user signup, login, and admin operations
"""

from fastapi import APIRouter, HTTPException, status, Header, Query
from typing import Optional
from app.adapters.http.schemas.user_schemas import (
    UserCreateRequest,
    AdminCreateUserRequest,
    UserLoginRequest,
    TokenResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# This will be injected by main.py
auth_service = None


def set_auth_service(service):
    """Set the authentication service (called from main.py)"""
    global auth_service
    auth_service = service


@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserCreateRequest):
    """
    Register a new CANDIDATE account (public signup)
    
    - **name**: User full name
    - **email**: User email (must be unique)
    - **password**: 8 characters minimum, 72 UTF-8 bytes maximum, including one letter and one special character
    
    Note: All new accounts are created as 'candidate' role
    """
    try:
        result = await auth_service.register_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during signup"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginRequest):
    """
    Authenticate user and get JWT token
    
    - **email**: User email
    - **password**: 8 characters minimum, 72 UTF-8 bytes maximum, including one letter and one special character
    """
    try:
        result = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )


@router.post("/admin/create-user", response_model=TokenResponse)
async def create_user_as_admin(
    user_data: AdminCreateUserRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new HR or ADMIN user (admin only)
    
    Requires valid JWT token from admin user in Authorization header:
    `Authorization: Bearer <token>`
    
    - **name**: User full name
    - **email**: User email (must be unique)
    - **password**: User password
    - **role**: 'hr' or 'admin'
    """
    # Extract token from header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    # Verify token
    payload = auth_service.token_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Check if user is admin
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    try:
        result = await auth_service.create_user_as_admin(
            admin_email=payload.get("email"),
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role.value
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.get("/admin/users")
async def list_users_as_admin(
    role: Optional[str] = Query(None, pattern="^(hr|admin|candidate)$"),
    authorization: Optional[str] = Header(None),
):
    """List users, optionally filtered by role (admin only)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    payload = auth_service.token_service.verify_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list users",
        )

    try:
        return await auth_service.list_users_as_admin(payload.get("email"), role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing users",
        )
