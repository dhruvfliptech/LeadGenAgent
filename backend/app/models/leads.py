"""
Enhanced Lead model with complete metadata capture.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class Lead(Base):
    """Enhanced Lead model for storing scraped leads with complete metadata."""
    
    __tablename__ = "leads"
    
    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Craigslist identifiers
    craigslist_id = Column(String(50), unique=True, nullable=False, index=True)
    url = Column(Text, nullable=False)
    
    # Content fields
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)  # NEW: Full HTML content
    
    # Timestamps
    posted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Job/Gig details
    price = Column(Float, nullable=True)
    compensation = Column(String(255), nullable=True, index=True)  # NEW: Compensation text
    employment_type = Column(ARRAY(String), nullable=True)  # NEW: Multiple employment types
    is_remote = Column(Boolean, default=False, nullable=False, index=True)  # NEW
    is_internship = Column(Boolean, default=False, nullable=False)  # NEW
    is_nonprofit = Column(Boolean, default=False, nullable=False)  # NEW
    
    # Location information
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    location = relationship("Location", backref="leads")
    neighborhood = Column(String(255), nullable=True)  # NEW: Specific neighborhood
    latitude = Column(Float, nullable=True)  # NEW: GPS coordinates
    longitude = Column(Float, nullable=True)  # NEW: GPS coordinates
    
    # Contact information
    email = Column(String(255), nullable=True, index=True)  # Existing but enhanced
    email_source = Column(String(50), nullable=True, index=True)  # hunter_io, rocketreach, scraped, manual
    phone = Column(String(50), nullable=True, index=True)
    contact_name = Column(String(255), nullable=True)
    reply_email = Column(String(255), nullable=True, index=True)  # NEW: Reply-to email
    reply_phone = Column(String(50), nullable=True)  # NEW: Reply-to phone
    reply_contact_name = Column(String(255), nullable=True)  # NEW: Reply contact name
    
    # Media
    image_urls = Column(JSON, nullable=True)  # NEW: Array of image URLs
    
    # Additional attributes
    attributes = Column(JSON, nullable=True)  # NEW: Flexible key-value attributes

    # Source tracking (Phase 2: Multi-source leads)
    source = Column(String(50), default="craigslist", nullable=False, index=True)
    # Source values: craigslist, google_maps, google_places_api, linkedin, indeed, monster, ziprecruiter

    # Categorization
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True, index=True)

    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    is_contacted = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(String(50), default="new", nullable=False, index=True)
    # Status values: new, qualified, contacted, responded, converted, rejected
    
    # AI Analysis fields (NEW)
    qualification_score = Column(Float, nullable=True, index=True)  # 0.0 to 1.0
    qualification_reasoning = Column(Text, nullable=True)  # AI's reasoning
    generated_responses = Column(JSON, nullable=True)  # Array of generated responses

    # AI MVP fields (Website Analysis + Email Generation)
    ai_analysis = Column(Text, nullable=True)  # Full AI website analysis
    ai_model = Column(String(100), nullable=True)  # Model used for analysis
    ai_cost = Column(Float, nullable=True)  # Cost of AI analysis
    ai_request_id = Column(Integer, nullable=True)  # AI-GYM request ID
    generated_email_subject = Column(Text, nullable=True)  # Generated email subject
    generated_email_body = Column(Text, nullable=True)  # Generated email body
    
    # Tracking fields (NEW)
    has_been_qualified = Column(Boolean, default=False, nullable=False, index=True)
    qualified_at = Column(DateTime(timezone=True), nullable=True)
    response_sent_at = Column(DateTime(timezone=True), nullable=True)
    response_method = Column(String(50), nullable=True)  # email, craigslist_reply, etc.
    
    def __repr__(self):
        return f"<Lead(id={self.id}, craigslist_id='{self.craigslist_id}', title='{self.title[:50]}...', score={self.qualification_score})>"
    
    def to_dict(self):
        """Convert lead to dictionary for API responses."""
        return {
            'id': self.id,
            'craigslist_id': self.craigslist_id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'compensation': self.compensation,
            'employment_type': self.employment_type,
            'is_remote': self.is_remote,
            'is_internship': self.is_internship,
            'is_nonprofit': self.is_nonprofit,
            'location': {
                'id': self.location_id,
                'name': self.location.name if self.location else None,
                'neighborhood': self.neighborhood,
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'contact': {
                'email': self.email,
                'phone': self.phone,
                'contact_name': self.contact_name,
                'reply_email': self.reply_email,
                'reply_phone': self.reply_phone,
                'reply_contact_name': self.reply_contact_name
            },
            'media': {
                'image_urls': self.image_urls or []
            },
            'attributes': self.attributes or {},
            'category': self.category,
            'subcategory': self.subcategory,
            'status': self.status,
            'ai_analysis': {
                'qualification_score': self.qualification_score,
                'qualification_reasoning': self.qualification_reasoning,
                'has_been_qualified': self.has_been_qualified,
                'qualified_at': self.qualified_at.isoformat() if self.qualified_at else None
            },
            'timestamps': {
                'posted_at': self.posted_at.isoformat() if self.posted_at else None,
                'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'response_sent_at': self.response_sent_at.isoformat() if self.response_sent_at else None
            }
        }