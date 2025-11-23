"""
Middleware module.
"""

from .event_emitter import setup_event_listeners, emit_webhook_event

__all__ = ["setup_event_listeners", "emit_webhook_event"]
