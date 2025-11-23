"""
AI-GYM: Multi-Model AI Optimization System

The secret sauce that enables intelligent model selection, performance tracking,
A/B testing, and continuous optimization across GPT-4, Claude, Qwen, and Grok.

Key Components:
- Model Registry: Track available models with capabilities and costs
- Model Router: Smart routing to optimal model for each task
- Metric Tracker: Record performance metrics for every AI call
- A/B Testing: Compare models head-to-head
- Quality Scoring: Automated quality assessment
"""

from typing import Optional
from .models import AIModel, ModelRegistry, get_model_registry
from .router import ModelRouter, get_model_router
from .tracker import MetricTracker, get_metric_tracker
from .ab_testing import ABTestManager, get_ab_test_manager
from .quality import QualityScorer, get_quality_scorer

__all__ = [
    "AIModel",
    "ModelRegistry",
    "ModelRouter",
    "MetricTracker",
    "ABTestManager",
    "QualityScorer",
    "get_model_registry",
    "get_model_router",
    "get_metric_tracker",
    "get_ab_test_manager",
    "get_quality_scorer",
]

# Version
__version__ = "1.0.0"
