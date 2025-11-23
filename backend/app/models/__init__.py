"""
Database models module.
"""

from .base import Base

from .locations import Location
from .leads import Lead
from .feedback import LeadFeedback, ModelMetrics, ABTestVariant
from .qualification_criteria import QualificationCriteria
from .response_templates import ResponseTemplate
from .approvals import ResponseApproval, ApprovalRule, ApprovalQueue, ApprovalHistory
from .learning import InteractionFeedback, LearningState, RewardSignal, FeatureImportance, PolicyHistory
from .memory import ConversationMemory, ShortTermMemory, LongTermMemory, SemanticMemory, EpisodicMemory, ContextState
from .conversation import Conversation, ConversationMessage, AISuggestion, ConversationStatus, MessageDirection, SuggestionStatus
from .email_finder import EmailFinderUsage, FoundEmail, EmailFinderQuota, EmailSource, ServiceName
from .demo_sites import (
    DemoSite, DeploymentHistory, DemoSiteTemplate, DemoSiteAnalytics, DemoSiteComponent,
    DeploymentStatus, DeploymentFramework
)
from .video_scripts import VideoScript
from .voiceovers import Voiceover, VoiceoverUsage, VoiceoverCache, VoiceoverStatus, AudioFormat
from .screen_recordings import ScreenRecording, RecordingSession, RecordingSegment, RecordingStatus, VideoFormat, VideoQuality
from .composed_videos import ComposedVideo, CompositionJob, CompositionStatus
from .webhook_queue import WebhookQueueItem, WebhookLog, WebhookRetryHistory, WebhookStatus, WebhookDirection
from .users import User, UserSession, AuditLog, PasswordHistory, PERMISSIONS, ROLES
from .campaigns import Campaign, CampaignRecipient, EmailTracking
from .knowledge_base import KnowledgeBaseEntry, EntryType  # KnowledgeBaseEmbedding removed - pgvector not available
from .tags import Tag, LeadTag
from .notes import Note
from .website_analysis import WebsiteAnalysis, AnalysisStatus, AnalysisDepth
from .linkedin_contacts import LinkedInContact, LinkedInMessage, LinkedInConnection
from .hosted_videos import HostedVideo, VideoView, HostingProvider, VideoStatus, VideoPrivacy
from .n8n_workflows import (
    N8NWorkflow, WorkflowExecution, WorkflowApproval, WebhookQueue, WorkflowMonitoring,
    WorkflowStatus, ApprovalStatus, ApprovalPriority, QueueStatus, MonitoringSeverity
)
from .auto_response import AutoResponse, ResponseVariable
from .campaign_metrics import CampaignMetrics, CampaignMetricsSnapshot
from .ai_gym import AIGymPerformance

__all__ = [
    "Base",
    "Location",
    "Lead",
    "LeadFeedback",
    "ModelMetrics",
    "ABTestVariant",
    "QualificationCriteria",
    "ResponseTemplate",
    "ResponseApproval",
    "ApprovalRule",
    "ApprovalQueue",
    "ApprovalHistory",
    "InteractionFeedback",
    "LearningState",
    "RewardSignal",
    "FeatureImportance",
    "PolicyHistory",
    "ConversationMemory",
    "ShortTermMemory",
    "LongTermMemory",
    "SemanticMemory",
    "EpisodicMemory",
    "ContextState",
    "Conversation",
    "ConversationMessage",
    "AISuggestion",
    "ConversationStatus",
    "MessageDirection",
    "SuggestionStatus",
    "EmailFinderUsage",
    "FoundEmail",
    "EmailFinderQuota",
    "EmailSource",
    "ServiceName",
    "DemoSite",
    "DeploymentHistory",
    "DemoSiteTemplate",
    "DemoSiteAnalytics",
    "DemoSiteComponent",
    "DeploymentStatus",
    "DeploymentFramework",
    "VideoScript",
    "Voiceover",
    "VoiceoverUsage",
    "VoiceoverCache",
    "VoiceoverStatus",
    "AudioFormat",
    "ScreenRecording",
    "RecordingSession",
    "RecordingSegment",
    "RecordingStatus",
    "VideoFormat",
    "VideoQuality",
    "ComposedVideo",
    "CompositionJob",
    "CompositionStatus",
    "WebhookQueueItem",
    "WebhookLog",
    "WebhookRetryHistory",
    "WebhookStatus",
    "WebhookDirection",
    "User",
    "UserSession",
    "AuditLog",
    "PasswordHistory",
    "PERMISSIONS",
    "ROLES",
    "Campaign",
    "CampaignRecipient",
    "EmailTracking",
    "KnowledgeBaseEntry",
    # "KnowledgeBaseEmbedding",  # Removed - pgvector not available
    "EntryType",
    "Tag",
    "LeadTag",
    "Note",
    "WebsiteAnalysis",
    "AnalysisStatus",
    "AnalysisDepth",
    "LinkedInContact",
    "LinkedInMessage",
    "LinkedInConnection",
    "HostedVideo",
    "VideoView",
    "HostingProvider",
    "VideoStatus",
    "VideoPrivacy",
    "N8NWorkflow",
    "WorkflowExecution",
    "WorkflowApproval",
    "WebhookQueue",
    "WorkflowMonitoring",
    "WorkflowStatus",
    "ApprovalStatus",
    "ApprovalPriority",
    "QueueStatus",
    "MonitoringSeverity",
    "AutoResponse",
    "ResponseVariable",
    "CampaignMetrics",
    "CampaignMetricsSnapshot",
    "AIGymPerformance"
]