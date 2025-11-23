"""
Rule engine models for advanced filtering and automation.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
from enum import Enum
from typing import Dict, Any, List


class RuleOperator(str, Enum):
    """Rule operators for conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class RuleLogic(str, Enum):
    """Logic operators for combining rules."""
    AND = "and"
    OR = "or"
    NOT = "not"


class RuleAction(str, Enum):
    """Actions to take when rule matches."""
    ACCEPT = "accept"
    REJECT = "reject"
    PRIORITY_HIGH = "priority_high"
    PRIORITY_LOW = "priority_low"
    AUTO_RESPOND = "auto_respond"
    NOTIFY = "notify"
    TAG = "tag"
    ASSIGN = "assign"


class FilterRule(Base):
    """Advanced filtering rule for leads."""
    
    __tablename__ = "filter_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rule metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # filtering, automation, notification
    
    # Rule configuration
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False, index=True)  # Lower = higher priority
    
    # Condition configuration
    field_name = Column(String(100), nullable=False)  # lead field to evaluate
    operator = Column(String(50), nullable=False)  # RuleOperator
    value = Column(Text, nullable=True)  # Value to compare against
    value_list = Column(JSON, nullable=True)  # For list-based operators
    regex_pattern = Column(String(500), nullable=True)  # For regex matching
    
    # Numeric range conditions
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Action configuration
    action = Column(String(50), nullable=False)  # RuleAction
    action_config = Column(JSON, nullable=True)  # Additional action parameters
    
    # Performance tracking
    evaluation_count = Column(Integer, default=0, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    @property
    def match_rate(self) -> float:
        """Calculate rule match rate percentage."""
        if self.evaluation_count == 0:
            return 0.0
        return (self.match_count / self.evaluation_count) * 100
    
    def __repr__(self):
        return f"<FilterRule(id={self.id}, name='{self.name}', field='{self.field_name}', action='{self.action}')>"


class RuleSet(Base):
    """Collection of rules with logic operators."""
    
    __tablename__ = "rule_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rule set metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False, index=True)
    logic_operator = Column(String(10), default="and", nullable=False)  # RuleLogic
    
    # Performance tracking
    evaluation_count = Column(Integer, default=0, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    rules = relationship("FilterRule", secondary="rule_set_rules", backref="rule_sets")
    
    @property
    def match_rate(self) -> float:
        """Calculate rule set match rate percentage."""
        if self.evaluation_count == 0:
            return 0.0
        return (self.match_count / self.evaluation_count) * 100
    
    def __repr__(self):
        return f"<RuleSet(id={self.id}, name='{self.name}', logic='{self.logic_operator}')>"


class RuleSetRule(Base):
    """Many-to-many relationship between rule sets and rules."""
    
    __tablename__ = "rule_set_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_set_id = Column(Integer, ForeignKey("rule_sets.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("filter_rules.id"), nullable=False)
    order_index = Column(Integer, default=0, nullable=False)  # Order within rule set
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExcludeList(Base):
    """Exclude list for filtering out unwanted leads."""
    
    __tablename__ = "exclude_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # List metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    list_type = Column(String(50), nullable=False, index=True)  # email, phone, keyword, domain
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_case_sensitive = Column(Boolean, default=False, nullable=False)
    match_type = Column(String(50), default="exact", nullable=False)  # exact, partial, regex
    
    # Performance tracking
    match_count = Column(Integer, default=0, nullable=False)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ExcludeList(id={self.id}, name='{self.name}', type='{self.list_type}')>"


class ExcludeListItem(Base):
    """Individual items in exclude lists."""
    
    __tablename__ = "exclude_list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # List reference
    exclude_list_id = Column(Integer, ForeignKey("exclude_lists.id"), nullable=False, index=True)
    
    # Item data
    value = Column(String(500), nullable=False, index=True)
    pattern = Column(String(500), nullable=True)  # For regex patterns
    notes = Column(Text, nullable=True)
    
    # Performance tracking
    match_count = Column(Integer, default=0, nullable=False)
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    exclude_list = relationship("ExcludeList", backref="items")
    
    def __repr__(self):
        return f"<ExcludeListItem(id={self.id}, value='{self.value}', list_id={self.exclude_list_id})>"


class RuleExecution(Base):
    """Log of rule executions for debugging and analytics."""
    
    __tablename__ = "rule_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Execution context
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("filter_rules.id"), nullable=True, index=True)
    rule_set_id = Column(Integer, ForeignKey("rule_sets.id"), nullable=True, index=True)
    
    # Execution results
    matched = Column(Boolean, nullable=False, index=True)
    action_taken = Column(String(50), nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    
    # Debug information
    evaluation_data = Column(JSON, nullable=True)  # Field values at time of evaluation
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    lead = relationship("Lead", backref="rule_executions")
    rule = relationship("FilterRule", backref="executions")
    rule_set = relationship("RuleSet", backref="executions")
    
    def __repr__(self):
        return f"<RuleExecution(id={self.id}, lead_id={self.lead_id}, matched={self.matched})>"