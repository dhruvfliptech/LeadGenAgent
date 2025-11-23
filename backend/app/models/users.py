"""
User model for authentication and authorization.
Implements secure user data storage per OWASP guidelines.
NOTE: This is a placeholder model. Migrations are not created yet.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List, Optional
import secrets

from app.models import Base


class User(Base):
    """
    User model for authentication.
    Follows OWASP best practices for user data storage.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    email = Column(String(254), unique=True, index=True, nullable=False)  # RFC 5321 max email length
    password_hash = Column(String(255), nullable=False)  # Bcrypt hash

    # User information
    full_name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Email verification
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 max length
    password_changed_at = Column(DateTime(timezone=True), default=func.now())

    # Two-factor authentication
    totp_secret = Column(String(32), nullable=True)  # For TOTP 2FA
    backup_codes = Column(JSON, nullable=True)  # Encrypted backup codes
    two_factor_enabled = Column(Boolean, default=False, nullable=False)

    # API access
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    api_rate_limit = Column(Integer, default=1000, nullable=False)  # Requests per hour

    # Permissions and roles (JSON for flexibility)
    permissions = Column(JSON, default=list, nullable=False)
    roles = Column(JSON, default=list, nullable=False)

    # Password reset
    reset_token = Column(String(255), nullable=True, unique=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Email verification
    verification_token = Column(String(255), nullable=True, unique=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    created_by = Column(Integer, nullable=True)  # User ID who created this account
    notes = Column(Text, nullable=True)  # Admin notes

    # Relationships (when other models are ready)
    # sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    # audit_logs = relationship("AuditLog", back_populates="user")
    # notifications = relationship("Notification", back_populates="user")

    def generate_api_key(self) -> str:
        """Generate a new API key for the user."""
        self.api_key = secrets.token_urlsafe(48)
        self.api_key_created_at = func.now()
        return self.api_key

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in (self.permissions or [])

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in (self.roles or [])

    def add_permission(self, permission: str):
        """Add a permission to the user."""
        if not self.permissions:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str):
        """Remove a permission from the user."""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)

    def add_role(self, role: str):
        """Add a role to the user."""
        if not self.roles:
            self.roles = []
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: str):
        """Remove a role from the user."""
        if self.roles and role in self.roles:
            self.roles.remove(role)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"


class UserSession(Base):
    """
    Track user sessions for security and audit purposes.
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True)

    # Session metadata
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(64), nullable=True)  # Hash of device characteristics

    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    # user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class AuditLog(Base):
    """
    Audit log for tracking user actions and security events.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Nullable for system events

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, password_change, etc.
    event_category = Column(String(50), nullable=False)  # auth, data, admin, security
    event_description = Column(Text, nullable=False)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)

    # Response
    response_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)

    # Additional data
    event_metadata = Column(JSON, nullable=True)  # Additional event-specific data

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    # user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event={self.event_type}, user_id={self.user_id})>"


class PasswordHistory(Base):
    """
    Track password history to prevent reuse.
    """
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Store hash of old password (never plain text)
    password_hash = Column(String(255), nullable=False)

    # When it was used
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<PasswordHistory(id={self.id}, user_id={self.user_id})>"


# Permission constants (for reference)
PERMISSIONS = {
    # Lead management
    "leads:read": "View leads",
    "leads:write": "Create and update leads",
    "leads:delete": "Delete leads",

    # Scraper management
    "scraper:run": "Run scraper jobs",
    "scraper:configure": "Configure scraper settings",

    # ML/AI features
    "ml:score": "Use ML scoring",
    "ml:train": "Train ML models",
    "ai:generate": "Generate AI responses",

    # Admin permissions
    "admin:users": "Manage users",
    "admin:settings": "Manage system settings",
    "admin:audit": "View audit logs",

    # API access
    "api:full": "Full API access",
    "api:read": "Read-only API access",
}

# Role definitions (for reference)
ROLES = {
    "viewer": ["leads:read", "ml:score"],
    "operator": ["leads:read", "leads:write", "scraper:run", "ml:score", "ai:generate"],
    "manager": ["leads:read", "leads:write", "leads:delete", "scraper:run", "scraper:configure", "ml:score", "ml:train", "ai:generate"],
    "admin": list(PERMISSIONS.keys()),  # All permissions
}


__all__ = [
    'User',
    'UserSession',
    'AuditLog',
    'PasswordHistory',
    'PERMISSIONS',
    'ROLES'
]