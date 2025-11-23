"""
Video services module for screen recording and interaction generation.
"""

from .screen_recorder import (
    ScreenRecorder,
    RecordingConfig,
    Interaction,
    InteractionSequence,
    RecordingResult,
    RecordingQualityPresets
)
from .interaction_generator import (
    InteractionGenerator,
    ElementInfo,
    ScriptSection,
    VideoScript,
    InteractionTemplates
)

__all__ = [
    "ScreenRecorder",
    "RecordingConfig",
    "Interaction",
    "InteractionSequence",
    "RecordingResult",
    "RecordingQualityPresets",
    "InteractionGenerator",
    "ElementInfo",
    "ScriptSection",
    "VideoScript",
    "InteractionTemplates"
]
