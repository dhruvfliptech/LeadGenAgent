"""
Feedback processing service for incremental learning and user interaction handling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import structlog
import numpy as np

from app.models.leads import Lead
from app.models.feedback import LeadFeedback, ModelMetrics, ABTestVariant
from app.ml.lead_scorer import LeadScorer

logger = structlog.get_logger(__name__)


class FeedbackProcessor:
    """Process user feedback and interactions for incremental learning."""
    
    def __init__(self):
        self.scorer = None
        self.ab_test_cache = {}
        
        # Feedback processing rules
        self.confidence_thresholds = {
            'explicit_rating': 1.0,  # Direct user rating
            'conversion': 0.95,      # Successful conversion
            'contact_success': 0.9,  # Successful contact
            'contact_attempt': 0.7,  # Contact attempted
            'long_view': 0.6,        # Viewed for >2 minutes
            'quick_archive': 0.8,    # Quickly archived (negative signal)
            'short_view': 0.3        # Brief view
        }
        
        # Automatic feedback generation rules
        self.auto_feedback_rules = {
            'view_duration': {
                'high_engagement': 300,  # 5+ minutes
                'medium_engagement': 120, # 2+ minutes
                'low_engagement': 30     # 30+ seconds
            },
            'interaction_patterns': {
                'multiple_views': 3,     # Viewed 3+ times
                'quick_archive_time': 10 # Archived within 10 seconds
            }
        }
    
    async def process_user_feedback(self, db: Session, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process explicit user feedback."""
        try:
            logger.info("Processing user feedback", 
                       lead_id=feedback_data.get('lead_id'),
                       action=feedback_data.get('action_type'))
            
            # Validate required fields
            required_fields = ['lead_id', 'action_type']
            for field in required_fields:
                if not feedback_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Get the lead
            lead = db.query(Lead).filter(Lead.id == feedback_data['lead_id']).first()
            if not lead:
                raise ValueError(f"Lead {feedback_data['lead_id']} not found")
            
            # Determine feedback confidence
            action_type = feedback_data['action_type']
            confidence = self._calculate_feedback_confidence(action_type, feedback_data)
            
            # Get current model prediction if available
            prediction_score = await self._get_current_prediction(db, lead.id)
            
            # Create feedback record
            feedback = LeadFeedback(
                lead_id=feedback_data['lead_id'],
                user_rating=feedback_data.get('user_rating'),
                action_type=action_type,
                interaction_duration=feedback_data.get('interaction_duration'),
                feedback_source='manual',
                feedback_confidence=confidence,
                contact_successful=feedback_data.get('contact_successful'),
                contact_response_time=feedback_data.get('contact_response_time'),
                conversion_value=feedback_data.get('conversion_value'),
                session_id=feedback_data.get('session_id'),
                user_agent=feedback_data.get('user_agent'),
                ip_address=feedback_data.get('ip_address'),
                prediction_score=prediction_score
            )
            
            db.add(feedback)
            db.commit()
            
            # Update lead status based on feedback
            await self._update_lead_status(db, lead, action_type, feedback_data)
            
            # Check if we should trigger incremental learning
            await self._check_incremental_learning(db, feedback)
            
            logger.info("User feedback processed", 
                       feedback_id=feedback.id,
                       confidence=confidence)
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'confidence': confidence,
                'prediction_score': prediction_score,
                'message': 'Feedback processed successfully'
            }
            
        except Exception as e:
            logger.error("Error processing user feedback", 
                        lead_id=feedback_data.get('lead_id'),
                        error=str(e))
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process feedback'
            }
    
    async def generate_implicit_feedback(self, db: Session, 
                                       session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate implicit feedback from user interaction patterns."""
        try:
            logger.info("Generating implicit feedback", 
                       session_id=session_data.get('session_id'))
            
            session_id = session_data.get('session_id')
            if not session_id:
                return []
            
            # Analyze interaction patterns
            interactions = session_data.get('interactions', [])
            implicit_feedback = []
            
            for interaction in interactions:
                lead_id = interaction.get('lead_id')
                if not lead_id:
                    continue
                
                feedback = await self._analyze_interaction_pattern(db, interaction)
                if feedback:
                    feedback['session_id'] = session_id
                    feedback['lead_id'] = lead_id
                    implicit_feedback.append(feedback)
            
            # Store implicit feedback
            stored_feedback = []
            for fb_data in implicit_feedback:
                feedback = LeadFeedback(
                    lead_id=fb_data['lead_id'],
                    action_type=fb_data['action_type'],
                    interaction_duration=fb_data.get('interaction_duration'),
                    feedback_source='implicit',
                    feedback_confidence=fb_data['confidence'],
                    session_id=fb_data['session_id'],
                    prediction_score=await self._get_current_prediction(db, fb_data['lead_id'])
                )
                
                db.add(feedback)
                stored_feedback.append(feedback)
            
            db.commit()
            
            logger.info("Implicit feedback generated", 
                       count=len(stored_feedback))
            
            return [
                {
                    'feedback_id': fb.id,
                    'lead_id': fb.lead_id,
                    'action_type': fb.action_type,
                    'confidence': fb.feedback_confidence
                }
                for fb in stored_feedback
            ]
            
        except Exception as e:
            logger.error("Error generating implicit feedback", error=str(e))
            return []
    
    async def _analyze_interaction_pattern(self, db: Session, 
                                         interaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze individual interaction to generate feedback."""
        try:
            interaction_type = interaction.get('type')
            duration = interaction.get('duration', 0)
            lead_id = interaction.get('lead_id')
            
            # View duration analysis
            if interaction_type == 'view':
                if duration >= self.auto_feedback_rules['view_duration']['high_engagement']:
                    return {
                        'action_type': 'view',
                        'interaction_duration': duration,
                        'confidence': self.confidence_thresholds['long_view']
                    }
                elif duration <= self.auto_feedback_rules['view_duration']['low_engagement']:
                    return {
                        'action_type': 'view',
                        'interaction_duration': duration,
                        'confidence': self.confidence_thresholds['short_view']
                    }
            
            # Quick archive detection
            elif interaction_type == 'archive':
                if duration <= self.auto_feedback_rules['interaction_patterns']['quick_archive_time']:
                    return {
                        'action_type': 'archive',
                        'interaction_duration': duration,
                        'confidence': self.confidence_thresholds['quick_archive']
                    }
            
            # Multiple view detection
            elif interaction_type == 'multiple_views':
                view_count = interaction.get('view_count', 0)
                if view_count >= self.auto_feedback_rules['interaction_patterns']['multiple_views']:
                    return {
                        'action_type': 'view',
                        'interaction_duration': duration,
                        'confidence': 0.7  # High interest indicated by multiple views
                    }
            
            return None
            
        except Exception as e:
            logger.error("Error analyzing interaction pattern", error=str(e))
            return None
    
    def _calculate_feedback_confidence(self, action_type: str, 
                                     feedback_data: Dict[str, Any]) -> float:
        """Calculate confidence level for feedback."""
        
        if feedback_data.get('user_rating') is not None:
            return self.confidence_thresholds['explicit_rating']
        
        confidence_map = {
            'convert': self.confidence_thresholds['conversion'],
            'contact': (self.confidence_thresholds['contact_success'] 
                       if feedback_data.get('contact_successful') 
                       else self.confidence_thresholds['contact_attempt']),
            'view': (self.confidence_thresholds['long_view'] 
                    if feedback_data.get('interaction_duration', 0) > 120 
                    else self.confidence_thresholds['short_view']),
            'archive': self.confidence_thresholds['quick_archive'],
            'rate': self.confidence_thresholds['explicit_rating']
        }
        
        return confidence_map.get(action_type, 0.5)
    
    async def _get_current_prediction(self, db: Session, lead_id: int) -> Optional[float]:
        """Get current model prediction for a lead."""
        try:
            # This would typically involve loading the current model and predicting
            # For now, we'll return None and let the API endpoint handle predictions
            return None
        except Exception as e:
            logger.warning("Could not get current prediction", 
                          lead_id=lead_id, 
                          error=str(e))
            return None
    
    async def _update_lead_status(self, db: Session, lead: Lead, 
                                action_type: str, feedback_data: Dict[str, Any]) -> None:
        """Update lead status based on feedback."""
        try:
            status_updates = {
                'contact': 'contacted',
                'convert': 'converted',
                'archive': 'rejected'
            }
            
            new_status = status_updates.get(action_type)
            if new_status and lead.status != new_status:
                lead.status = new_status
                
                # Update contact flag
                if action_type == 'contact':
                    lead.is_contacted = True
                
                db.commit()
                
                logger.info("Lead status updated", 
                           lead_id=lead.id,
                           old_status=lead.status,
                           new_status=new_status)
                
        except Exception as e:
            logger.error("Error updating lead status", 
                        lead_id=lead.id,
                        error=str(e))
    
    async def _check_incremental_learning(self, db: Session, 
                                        feedback: LeadFeedback) -> None:
        """Check if incremental learning should be triggered."""
        try:
            # Get recent feedback count
            recent_date = datetime.utcnow() - timedelta(hours=1)
            recent_feedback_count = db.query(LeadFeedback).filter(
                LeadFeedback.created_at >= recent_date
            ).count()
            
            # Trigger incremental learning if we have enough recent feedback
            if recent_feedback_count >= 10:  # Configurable threshold
                logger.info("Triggering incremental learning check", 
                           recent_feedback_count=recent_feedback_count)
                # This could trigger a background task for incremental learning
                # For now, we just log it
            
        except Exception as e:
            logger.error("Error checking incremental learning", error=str(e))
    
    async def get_feedback_analytics(self, db: Session, 
                                   days: int = 7) -> Dict[str, Any]:
        """Get feedback analytics for monitoring."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get feedback counts by action type
            feedback_counts = db.query(
                LeadFeedback.action_type,
                func.count(LeadFeedback.id)
            ).filter(
                LeadFeedback.created_at >= start_date
            ).group_by(LeadFeedback.action_type).all()
            
            # Get feedback by source
            source_counts = db.query(
                LeadFeedback.feedback_source,
                func.count(LeadFeedback.id)
            ).filter(
                LeadFeedback.created_at >= start_date
            ).group_by(LeadFeedback.feedback_source).all()
            
            # Get average confidence by action type
            confidence_avg = db.query(
                LeadFeedback.action_type,
                func.avg(LeadFeedback.feedback_confidence)
            ).filter(
                LeadFeedback.created_at >= start_date
            ).group_by(LeadFeedback.action_type).all()
            
            # Get conversion metrics
            total_feedback = db.query(LeadFeedback).filter(
                LeadFeedback.created_at >= start_date
            ).count()
            
            conversions = db.query(LeadFeedback).filter(
                and_(
                    LeadFeedback.created_at >= start_date,
                    LeadFeedback.action_type == 'convert'
                )
            ).count()
            
            contact_attempts = db.query(LeadFeedback).filter(
                and_(
                    LeadFeedback.created_at >= start_date,
                    LeadFeedback.action_type == 'contact'
                )
            ).count()
            
            successful_contacts = db.query(LeadFeedback).filter(
                and_(
                    LeadFeedback.created_at >= start_date,
                    LeadFeedback.action_type == 'contact',
                    LeadFeedback.contact_successful == True
                )
            ).count()
            
            return {
                'period_days': days,
                'total_feedback': total_feedback,
                'feedback_by_action': dict(feedback_counts),
                'feedback_by_source': dict(source_counts),
                'confidence_by_action': {
                    action: float(conf) for action, conf in confidence_avg
                },
                'conversion_metrics': {
                    'total_conversions': conversions,
                    'conversion_rate': conversions / total_feedback if total_feedback > 0 else 0,
                    'contact_attempts': contact_attempts,
                    'successful_contacts': successful_contacts,
                    'contact_success_rate': (successful_contacts / contact_attempts 
                                           if contact_attempts > 0 else 0)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error generating feedback analytics", error=str(e))
            return {
                'period_days': days,
                'total_feedback': 0,
                'feedback_by_action': {},
                'feedback_by_source': {},
                'confidence_by_action': {},
                'conversion_metrics': {},
                'error': str(e)
            }
    
    async def get_lead_feedback_history(self, db: Session, 
                                      lead_id: int) -> List[Dict[str, Any]]:
        """Get feedback history for a specific lead."""
        try:
            feedback_records = db.query(LeadFeedback).filter(
                LeadFeedback.lead_id == lead_id
            ).order_by(desc(LeadFeedback.created_at)).all()
            
            history = []
            for feedback in feedback_records:
                history.append({
                    'id': feedback.id,
                    'action_type': feedback.action_type,
                    'user_rating': feedback.user_rating,
                    'interaction_duration': feedback.interaction_duration,
                    'feedback_source': feedback.feedback_source,
                    'confidence': feedback.feedback_confidence,
                    'contact_successful': feedback.contact_successful,
                    'conversion_value': feedback.conversion_value,
                    'prediction_score': feedback.prediction_score,
                    'model_version': feedback.model_version,
                    'created_at': feedback.created_at.isoformat() if feedback.created_at else None
                })
            
            return history
            
        except Exception as e:
            logger.error("Error getting lead feedback history", 
                        lead_id=lead_id,
                        error=str(e))
            return []
    
    async def bulk_process_feedback(self, db: Session, 
                                  feedback_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple feedback records in batch."""
        try:
            logger.info("Processing bulk feedback", count=len(feedback_batch))
            
            processed_count = 0
            error_count = 0
            results = []
            
            for feedback_data in feedback_batch:
                try:
                    result = await self.process_user_feedback(db, feedback_data)
                    results.append(result)
                    
                    if result['success']:
                        processed_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    results.append({
                        'success': False,
                        'error': str(e),
                        'lead_id': feedback_data.get('lead_id')
                    })
            
            logger.info("Bulk feedback processing completed", 
                       processed=processed_count,
                       errors=error_count)
            
            return {
                'success': True,
                'processed_count': processed_count,
                'error_count': error_count,
                'total_count': len(feedback_batch),
                'results': results
            }
            
        except Exception as e:
            logger.error("Error processing bulk feedback", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'error_count': len(feedback_batch),
                'total_count': len(feedback_batch),
                'results': []
            }
    
    async def cleanup_old_feedback(self, db: Session, 
                                 retention_days: int = 365) -> Dict[str, Any]:
        """Clean up old feedback records to manage database size."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count records to be deleted
            old_feedback_count = db.query(LeadFeedback).filter(
                LeadFeedback.created_at < cutoff_date
            ).count()
            
            if old_feedback_count == 0:
                return {
                    'success': True,
                    'message': 'No old feedback to clean up',
                    'deleted_count': 0
                }
            
            # Delete old feedback records
            deleted_count = db.query(LeadFeedback).filter(
                LeadFeedback.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info("Old feedback cleaned up", 
                       deleted_count=deleted_count,
                       retention_days=retention_days)
            
            return {
                'success': True,
                'message': f'Deleted {deleted_count} old feedback records',
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            logger.error("Error cleaning up old feedback", error=str(e))
            db.rollback()
            return {
                'success': False,
                'error': str(e),
                'deleted_count': 0
            }