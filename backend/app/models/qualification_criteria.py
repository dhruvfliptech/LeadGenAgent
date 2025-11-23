"""
Lead Qualification Criteria model for defining scoring rules.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from app.models import Base


class QualificationCriteria(Base):
    """Model for storing lead qualification criteria and rules."""
    
    __tablename__ = "qualification_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Keyword matching
    required_keywords = Column(JSON, nullable=True)  # Must have all of these
    preferred_keywords = Column(JSON, nullable=True)  # Bonus points for these
    excluded_keywords = Column(JSON, nullable=True)  # Disqualify if found
    
    # Compensation criteria
    min_compensation = Column(Float, nullable=True)
    max_compensation = Column(Float, nullable=True)
    compensation_type = Column(String(50), nullable=True)  # hourly, salary, project
    
    # Location criteria
    preferred_locations = Column(JSON, nullable=True)  # List of location IDs or names
    max_distance_miles = Column(Float, nullable=True)
    remote_acceptable = Column(Boolean, default=True)
    
    # Employment type preferences
    preferred_employment_types = Column(JSON, nullable=True)  # full-time, part-time, etc.
    internship_acceptable = Column(Boolean, default=True)
    nonprofit_acceptable = Column(Boolean, default=True)
    
    # Scoring weights (0.0 to 1.0)
    keyword_weight = Column(Float, default=0.3)
    compensation_weight = Column(Float, default=0.2)
    location_weight = Column(Float, default=0.2)
    employment_type_weight = Column(Float, default=0.15)
    freshness_weight = Column(Float, default=0.15)  # How recent the posting is
    
    # Qualification thresholds
    min_score_threshold = Column(Float, default=0.5)  # Minimum score to be qualified
    auto_qualify_threshold = Column(Float, default=0.8)  # Auto-qualify without review
    auto_reject_threshold = Column(Float, default=0.2)  # Auto-reject below this
    
    # Additional criteria
    max_days_old = Column(Integer, default=7)  # Maximum age of posting in days
    require_contact_info = Column(Boolean, default=False)
    require_compensation_info = Column(Boolean, default=False)
    
    # Custom scoring rules (JSON)
    custom_rules = Column(JSON, nullable=True)
    """
    Example custom_rules:
    {
        "must_have_any": ["python", "javascript", "java"],
        "boost_if_contains": {
            "senior": 0.1,
            "lead": 0.1,
            "architect": 0.15
        },
        "penalty_if_contains": {
            "entry level": -0.2,
            "unpaid": -0.5
        }
    }
    """
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<QualificationCriteria(id={self.id}, name='{self.name}', threshold={self.min_score_threshold})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'keywords': {
                'required': self.required_keywords or [],
                'preferred': self.preferred_keywords or [],
                'excluded': self.excluded_keywords or []
            },
            'compensation': {
                'min': self.min_compensation,
                'max': self.max_compensation,
                'type': self.compensation_type
            },
            'location': {
                'preferred_locations': self.preferred_locations or [],
                'max_distance_miles': self.max_distance_miles,
                'remote_acceptable': self.remote_acceptable
            },
            'employment': {
                'preferred_types': self.preferred_employment_types or [],
                'internship_acceptable': self.internship_acceptable,
                'nonprofit_acceptable': self.nonprofit_acceptable
            },
            'weights': {
                'keyword': self.keyword_weight,
                'compensation': self.compensation_weight,
                'location': self.location_weight,
                'employment_type': self.employment_type_weight,
                'freshness': self.freshness_weight
            },
            'thresholds': {
                'min_score': self.min_score_threshold,
                'auto_qualify': self.auto_qualify_threshold,
                'auto_reject': self.auto_reject_threshold
            },
            'requirements': {
                'max_days_old': self.max_days_old,
                'require_contact_info': self.require_contact_info,
                'require_compensation_info': self.require_compensation_info
            },
            'custom_rules': self.custom_rules or {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }