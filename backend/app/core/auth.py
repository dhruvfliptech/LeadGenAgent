"""
Authentication and authorization middleware.
Implements JWT token-based authentication with secure password hashing.
Follows OWASP authentication best practices.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
import secrets
import hashlib
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

# Security configurations per OWASP guidelines
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Password hashing configuration (bcrypt with appropriate cost factor)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # OWASP recommended minimum
)

# JWT Bearer token security
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data."""
    user_id: int
    email: str
    exp: datetime
    token_type: str = "access"
    permissions: List[str] = Field(default_factory=list)


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    full_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)


class PasswordReset(BaseModel):
    """Password reset request schema."""
    token: str
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    Uses timing-safe comparison to prevent timing attacks.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt with salt.
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength according to OWASP guidelines.
    Returns (is_valid, error_message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"

    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f"Password must not exceed {PASSWORD_MAX_LENGTH} characters"

    # Check for complexity requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numeric characters"

    # Check for common patterns (basic check)
    common_patterns = ["password", "12345", "qwerty", "admin", "letmein"]
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            return False, "Password contains common patterns and is too weak"

    return True, "Password is strong"


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with expiration.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access",
        "jti": secrets.token_urlsafe(16)  # JWT ID for tracking
    })

    # Ensure we have a secret key
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY must be set for JWT encoding")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh",
        "jti": secrets.token_urlsafe(16)
    })

    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY must be set for JWT encoding")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    Returns TokenData if valid, None otherwise.
    """
    try:
        if not settings.SECRET_KEY:
            logger.error("SECRET_KEY not configured")
            return None

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("token_type") != token_type:
            logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('token_type')}")
            return None

        # Check expiration (jwt.decode handles this, but we double-check)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.info("Token expired")
            return None

        # Extract user data
        return TokenData(
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            exp=datetime.fromtimestamp(exp),
            token_type=payload.get("token_type"),
            permissions=payload.get("permissions", [])
        )

    except JWTError as e:
        logger.warning(f"JWT verification error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from JWT token.
    This is a placeholder that returns user data from the token.
    In production, this would fetch the full user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        token_data = verify_token(token)

        if token_data is None:
            raise credentials_exception

        # In a real implementation, fetch user from database
        # For now, return user data from token
        user = {
            "id": token_data.user_id,
            "email": token_data.email,
            "permissions": token_data.permissions,
            "is_active": True  # Would check database in production
        }

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to ensure the user is active.
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """
    Dependency factory for checking specific permissions.
    Usage: @router.get("/admin", dependencies=[Depends(require_permission("admin"))])
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ):
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user

    return permission_checker


class RateLimitedLogin:
    """
    Track login attempts to prevent brute force attacks.
    """

    def __init__(self):
        self.attempts = {}  # In production, use Redis
        self.lockouts = {}

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if login attempt is allowed.
        """
        now = datetime.utcnow()

        # Check if locked out
        if identifier in self.lockouts:
            lockout_until = self.lockouts[identifier]
            if now < lockout_until:
                remaining = (lockout_until - now).total_seconds()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account locked. Try again in {int(remaining)} seconds",
                    headers={"Retry-After": str(int(remaining))}
                )
            else:
                # Lockout expired
                del self.lockouts[identifier]
                self.attempts[identifier] = []

        return True

    def record_attempt(self, identifier: str, success: bool):
        """
        Record a login attempt.
        """
        now = datetime.utcnow()

        if identifier not in self.attempts:
            self.attempts[identifier] = []

        # Clean old attempts (older than 1 hour)
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if (now - attempt).total_seconds() < 3600
        ]

        if not success:
            self.attempts[identifier].append(now)

            # Check if we should lock out
            recent_attempts = [
                attempt for attempt in self.attempts[identifier]
                if (now - attempt).total_seconds() < 300  # Last 5 minutes
            ]

            if len(recent_attempts) >= MAX_LOGIN_ATTEMPTS:
                # Lock out the account
                self.lockouts[identifier] = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                logger.warning(f"Account locked due to too many failed attempts: {identifier}")
        else:
            # Clear attempts on successful login
            self.attempts[identifier] = []


# Global rate limiter for login attempts
login_rate_limiter = RateLimitedLogin()


def generate_password_reset_token(user_id: int, email: str) -> str:
    """
    Generate a secure password reset token.
    """
    data = {
        "user_id": user_id,
        "email": email,
        "purpose": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Also generate a shorter, user-friendly code
    reset_code = secrets.token_urlsafe(8)

    # In production, store the mapping in Redis
    # redis_client.setex(f"reset:{reset_code}", 3600, token)

    return reset_code


def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a password reset token.
    """
    try:
        # In production, lookup the full token from Redis using the short code
        # full_token = redis_client.get(f"reset:{token}")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("purpose") != "password_reset":
            return None

        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email")
        }

    except JWTError:
        return None


# Example endpoint protection decorators
def protected_endpoint(func):
    """
    Decorator to protect an endpoint with authentication.
    """
    async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


def admin_only(func):
    """
    Decorator to restrict endpoint to admin users.
    """
    async def wrapper(*args, current_user: Dict = Depends(require_permission("admin")), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


# Session management
class SessionManager:
    """
    Manage user sessions for additional security.
    """

    def __init__(self):
        self.active_sessions = {}  # In production, use Redis

    def create_session(self, user_id: int, token_jti: str) -> str:
        """
        Create a new session.
        """
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "token_jti": token_jti,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """
        Validate an active session.
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Check session timeout (1 hour of inactivity)
        if (datetime.utcnow() - session["last_activity"]).total_seconds() > 3600:
            del self.active_sessions[session_id]
            return False

        # Update last activity
        session["last_activity"] = datetime.utcnow()
        return True

    def invalidate_session(self, session_id: str):
        """
        Invalidate a session (logout).
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# Global session manager
session_manager = SessionManager()


__all__ = [
    'verify_password',
    'get_password_hash',
    'validate_password_strength',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'get_current_user',
    'get_current_active_user',
    'require_permission',
    'login_rate_limiter',
    'generate_password_reset_token',
    'verify_password_reset_token',
    'protected_endpoint',
    'admin_only',
    'session_manager',
    'UserLogin',
    'UserRegister',
    'PasswordReset',
    'Token',
    'TokenData'
]