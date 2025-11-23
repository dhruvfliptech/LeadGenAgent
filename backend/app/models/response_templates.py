"""
Response Template model for generating personalized responses.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from app.models import Base


class ResponseTemplate(Base):
    """Model for storing response templates with variable placeholders."""
    
    __tablename__ = "response_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Template content
    subject_template = Column("subject_template", Text, nullable=False)  # Email subject line
    body_template = Column("body_template", Text, nullable=False)  # Template body with variables
    
    # Legacy compatibility - map to old names
    @property
    def subject(self):
        return self.subject_template
    
    @subject.setter
    def subject(self, value):
        self.subject_template = value
    
    @property
    def body(self):
        return self.body_template
    
    @body.setter  
    def body(self, value):
        self.body_template = value
    
    # Category
    category = Column(String(100), nullable=True)
    
    # Variables used in this template
    variables = Column(JSON, nullable=True)  # Combined variables
    
    # AI Enhancement settings
    use_ai_enhancement = Column(Boolean, default=True)
    ai_tone = Column("ai_tone", String(50), default="professional")
    ai_length = Column("ai_length", String(50), default="medium")
    
    # A/B Testing
    is_test_variant = Column(Boolean, default=False)
    control_template_id = Column(Integer, nullable=True)
    test_weight = Column(Float, default=0.5)
    
    # Performance tracking
    sent_count = Column(Integer, default=0)
    response_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    
    # Properties for backward compatibility
    @property
    def template_type(self):
        return self.category or "general"
    
    @template_type.setter
    def template_type(self, value):
        self.category = value
    
    @property
    def communication_method(self):
        return "email"
    
    @property
    def required_variables(self):
        if self.variables and isinstance(self.variables, dict):
            return self.variables.get("required", [])
        return []
    
    @required_variables.setter
    def required_variables(self, value):
        if not self.variables:
            self.variables = {}
        self.variables["required"] = value
    
    @property
    def optional_variables(self):
        if self.variables and isinstance(self.variables, dict):
            return self.variables.get("optional", [])
        return []
    
    @optional_variables.setter
    def optional_variables(self, value):
        if not self.variables:
            self.variables = {}
        self.variables["optional"] = value
    
    @property
    def times_used(self):
        return self.sent_count
    
    @times_used.setter
    def times_used(self, value):
        self.sent_count = value
    
    @property
    def success_rate(self):
        if self.sent_count > 0:
            return (self.response_count / self.sent_count) * 100
        return None
    
    @property
    def avg_response_time(self):
        return None  # Not tracked in current schema
    
    @property
    def variant_group(self):
        return "test" if self.is_test_variant else None
    
    @property
    def variant_name(self):
        return f"variant_{self.id}" if self.is_test_variant else None
    
    @property
    def tone(self):
        return self.ai_tone
    
    @tone.setter
    def tone(self, value):
        self.ai_tone = value
    
    @property
    def length(self):
        return self.ai_length
    
    @length.setter
    def length(self, value):
        self.ai_length = value
    
    @property
    def ai_instructions(self):
        return None  # Not in current schema
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ResponseTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subject': self.subject,
            'body': self.body,
            'template_type': self.template_type,
            'communication_method': self.communication_method,
            'required_variables': self.required_variables or [],
            'optional_variables': self.optional_variables or [],
            'performance': {
                'times_used': self.times_used,
                'success_rate': self.success_rate,
                'avg_response_time': self.avg_response_time
            },
            'variant': {
                'group': self.variant_group,
                'name': self.variant_name
            },
            'customization': {
                'tone': self.tone,
                'length': self.length,
                'use_ai_enhancement': self.use_ai_enhancement,
                'ai_instructions': self.ai_instructions
            },
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Example template:
"""
Subject: Experienced {{user_profession}} Available for {{job_title}}

Body:
Hi {{contact_name|there}},

I saw your posting for {{job_title}} on Craigslist and I'm very interested in learning more about this opportunity.

{{if compensation}}
The compensation range of {{compensation}} aligns well with my expectations.
{{endif}}

I have {{years_experience}} years of experience in {{relevant_skills}}, including:
{{skill_list}}

{{if is_remote}}
I'm particularly interested as I work effectively in remote environments and have a proven track record of delivering results remotely.
{{endif}}

{{if company_name}}
I'm familiar with {{company_name}} and am excited about the possibility of contributing to your team.
{{endif}}

I'd love to discuss how my experience with {{key_qualification}} can contribute to your {{project_or_team}}.

I'm available for a conversation at your convenience. {{availability_statement}}

Best regards,
{{user_name}}
{{user_email}}
{{user_phone}}

{{if portfolio_url}}
Portfolio: {{portfolio_url}}
{{endif}}
"""