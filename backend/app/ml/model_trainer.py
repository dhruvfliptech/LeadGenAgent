"""
Model training and retraining pipeline with automated scheduling and performance monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import structlog
import pandas as pd

from app.core.database import get_db
from app.models.leads import Lead
from app.models.feedback import LeadFeedback, ModelMetrics, ABTestVariant
from app.ml.lead_scorer import LeadScorer

logger = structlog.get_logger(__name__)


class ModelTrainer:
    """Handles model training, retraining, and performance monitoring."""
    
    def __init__(self, model_dir: str = "/tmp/models"):
        self.model_dir = model_dir
        self.scorer = LeadScorer(model_dir)
        
        # Training configuration
        self.min_training_samples = 100
        self.min_feedback_samples = 50
        self.retrain_threshold_f1 = 0.05  # Retrain if F1 drops by 5%
        self.retrain_interval_days = 7
        
    async def check_retraining_needed(self, db: Session) -> Dict[str, Any]:
        """Check if model retraining is needed based on various criteria."""
        try:
            logger.info("Checking if retraining is needed")
            
            reasons = []
            should_retrain = False
            
            # Get current model metrics
            current_metrics = db.query(ModelMetrics).filter(
                ModelMetrics.is_active == True
            ).first()
            
            if not current_metrics:
                reasons.append("No active model found")
                should_retrain = True
            else:
                # Check model age
                if current_metrics.created_at:
                    model_age = datetime.utcnow() - current_metrics.created_at.replace(tzinfo=None)
                    if model_age > timedelta(days=self.retrain_interval_days):
                        reasons.append(f"Model is {model_age.days} days old")
                        should_retrain = True
                
                # Check for new feedback data
                last_train_date = current_metrics.created_at or datetime.utcnow() - timedelta(days=30)
                new_feedback_count = db.query(LeadFeedback).filter(
                    LeadFeedback.created_at > last_train_date
                ).count()
                
                if new_feedback_count >= self.min_feedback_samples:
                    reasons.append(f"New feedback available: {new_feedback_count} samples")
                    should_retrain = True
                
                # Check performance degradation (if we have recent performance data)
                recent_feedback = db.query(LeadFeedback).filter(
                    LeadFeedback.created_at >= datetime.utcnow() - timedelta(days=7),
                    LeadFeedback.model_version == current_metrics.model_version
                ).all()
                
                if len(recent_feedback) > 20:
                    recent_performance = self._calculate_recent_performance(recent_feedback)
                    if (current_metrics.f1_score and 
                        recent_performance['f1_score'] < current_metrics.f1_score - self.retrain_threshold_f1):
                        reasons.append(
                            f"Performance degradation: F1 dropped from "
                            f"{current_metrics.f1_score:.3f} to {recent_performance['f1_score']:.3f}"
                        )
                        should_retrain = True
            
            # Check data availability
            total_feedback = db.query(LeadFeedback).count()
            if total_feedback < self.min_training_samples:
                reasons.append(f"Insufficient training data: {total_feedback} < {self.min_training_samples}")
                should_retrain = False  # Can't train without enough data
            
            result = {
                'should_retrain': should_retrain,
                'reasons': reasons,
                'current_model_version': current_metrics.model_version if current_metrics else None,
                'feedback_count': total_feedback,
                'new_feedback_count': new_feedback_count if current_metrics else total_feedback
            }
            
            logger.info("Retraining check completed", 
                       should_retrain=should_retrain,
                       reasons_count=len(reasons))
            
            return result
            
        except Exception as e:
            logger.error("Error checking retraining need", error=str(e))
            return {
                'should_retrain': False,
                'reasons': [f"Error: {str(e)}"],
                'current_model_version': None,
                'feedback_count': 0,
                'new_feedback_count': 0
            }
    
    async def train_new_model(self, db: Session, 
                            params: Optional[Dict] = None,
                            validation_split: float = 0.2) -> Dict[str, Any]:
        """Train a new model with current data."""
        try:
            logger.info("Starting new model training")
            
            # Fetch training data
            leads_data = await self._fetch_leads_data(db)
            feedback_data = await self._fetch_feedback_data(db)
            
            logger.info("Training data fetched", 
                       leads_count=len(leads_data),
                       feedback_count=len(feedback_data))
            
            if len(feedback_data) < self.min_training_samples:
                raise ValueError(f"Insufficient training data: {len(feedback_data)} < {self.min_training_samples}")
            
            # Train model
            training_results = self.scorer.train(
                leads_data=leads_data,
                feedback_data=feedback_data,
                params=params,
                validation_split=validation_split
            )
            
            # Store metrics in database
            await self._store_model_metrics(db, training_results)
            
            # Deactivate old models
            db.query(ModelMetrics).update({'is_active': False})
            
            # Activate new model
            new_metrics = ModelMetrics(
                model_version=self.scorer.model_version,
                model_type='xgboost',
                precision=training_results['precision'],
                recall=training_results['recall'],
                f1_score=training_results['f1_score'],
                auc_roc=training_results['auc_roc'],
                accuracy=training_results['accuracy'],
                training_samples=training_results['training_samples'],
                validation_samples=training_results['validation_samples'],
                feature_count=training_results['feature_count'],
                training_duration=training_results['training_duration'],
                is_active=True,
                deployed_at=datetime.utcnow()
            )
            
            db.add(new_metrics)
            db.commit()
            
            logger.info("New model training completed", 
                       model_version=self.scorer.model_version,
                       f1_score=training_results['f1_score'])
            
            return {
                'success': True,
                'model_version': self.scorer.model_version,
                'metrics': training_results,
                'training_samples': len(feedback_data),
                'model_path': self.scorer.save_model()
            }
            
        except Exception as e:
            logger.error("Error training new model", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'model_version': None,
                'metrics': {},
                'training_samples': 0
            }
    
    async def retrain_model(self, db: Session, force: bool = False) -> Dict[str, Any]:
        """Retrain model if needed or forced."""
        try:
            if not force:
                retrain_check = await self.check_retraining_needed(db)
                if not retrain_check['should_retrain']:
                    return {
                        'success': True,
                        'retrained': False,
                        'reason': 'Retraining not needed',
                        'check_results': retrain_check
                    }
            
            # Perform retraining
            training_results = await self.train_new_model(db)
            
            if training_results['success']:
                return {
                    'success': True,
                    'retrained': True,
                    'reason': 'Model retrained successfully',
                    'training_results': training_results
                }
            else:
                return {
                    'success': False,
                    'retrained': False,
                    'reason': f"Retraining failed: {training_results['error']}",
                    'training_results': training_results
                }
                
        except Exception as e:
            logger.error("Error in retrain_model", error=str(e))
            return {
                'success': False,
                'retrained': False,
                'reason': f"Error: {str(e)}",
                'training_results': {}
            }
    
    async def _fetch_leads_data(self, db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch leads data for training."""
        try:
            query = db.query(Lead).join(LeadFeedback, Lead.id == LeadFeedback.lead_id)
            
            if limit:
                query = query.limit(limit)
            
            leads = query.all()
            
            leads_data = []
            for lead in leads:
                # Convert SQLAlchemy object to dict
                lead_dict = {
                    'id': lead.id,
                    'title': lead.title or '',
                    'description': lead.description or '',
                    'price': lead.price,
                    'email': lead.email,
                    'phone': lead.phone,
                    'contact_name': lead.contact_name,
                    'category': lead.category,
                    'subcategory': lead.subcategory,
                    'posted_at': lead.posted_at,
                    'scraped_at': lead.scraped_at,
                    'location': {
                        'name': lead.location.name if lead.location else None
                    }
                }
                leads_data.append(lead_dict)
            
            return leads_data
            
        except Exception as e:
            logger.error("Error fetching leads data", error=str(e))
            return []
    
    async def _fetch_feedback_data(self, db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch feedback data for training."""
        try:
            query = db.query(LeadFeedback)
            
            if limit:
                query = query.limit(limit)
            
            feedback = query.all()
            
            feedback_data = []
            for fb in feedback:
                feedback_dict = {
                    'id': fb.id,
                    'lead_id': fb.lead_id,
                    'user_rating': fb.user_rating,
                    'action_type': fb.action_type,
                    'interaction_duration': fb.interaction_duration,
                    'feedback_source': fb.feedback_source,
                    'feedback_confidence': fb.feedback_confidence,
                    'contact_successful': fb.contact_successful,
                    'contact_response_time': fb.contact_response_time,
                    'conversion_value': fb.conversion_value,
                    'created_at': fb.created_at
                }
                feedback_data.append(feedback_dict)
            
            return feedback_data
            
        except Exception as e:
            logger.error("Error fetching feedback data", error=str(e))
            return []
    
    async def _store_model_metrics(self, db: Session, metrics: Dict[str, Any]) -> None:
        """Store model training metrics."""
        try:
            # Calculate business metrics from recent feedback
            business_metrics = await self._calculate_business_metrics(db)
            
            # Update metrics with business data
            metrics.update(business_metrics)
            
        except Exception as e:
            logger.warning("Error calculating business metrics", error=str(e))
    
    async def _calculate_business_metrics(self, db: Session) -> Dict[str, float]:
        """Calculate business-relevant metrics."""
        try:
            # Get recent feedback for business metrics
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_feedback = db.query(LeadFeedback).filter(
                LeadFeedback.created_at >= recent_date
            ).all()
            
            if not recent_feedback:
                return {
                    'conversion_rate': 0.0,
                    'contact_success_rate': 0.0,
                    'avg_prediction_score': 50.0
                }
            
            # Calculate conversion rate
            conversions = [fb for fb in recent_feedback if fb.action_type == 'convert']
            conversion_rate = len(conversions) / len(recent_feedback)
            
            # Calculate contact success rate
            contacts = [fb for fb in recent_feedback if fb.action_type == 'contact']
            successful_contacts = [fb for fb in contacts if fb.contact_successful]
            contact_success_rate = len(successful_contacts) / len(contacts) if contacts else 0.0
            
            # Calculate average prediction score
            scores = [fb.prediction_score for fb in recent_feedback if fb.prediction_score is not None]
            avg_prediction_score = sum(scores) / len(scores) if scores else 50.0
            
            return {
                'conversion_rate': conversion_rate,
                'contact_success_rate': contact_success_rate,
                'avg_prediction_score': avg_prediction_score
            }
            
        except Exception as e:
            logger.error("Error calculating business metrics", error=str(e))
            return {
                'conversion_rate': 0.0,
                'contact_success_rate': 0.0,
                'avg_prediction_score': 50.0
            }
    
    def _calculate_recent_performance(self, feedback_list: List[LeadFeedback]) -> Dict[str, float]:
        """Calculate recent model performance from feedback."""
        try:
            if not feedback_list:
                return {'f1_score': 0.0, 'accuracy': 0.0}
            
            # Create binary labels based on feedback
            y_true = []
            y_pred = []
            
            for feedback in feedback_list:
                # Calculate true label based on feedback
                if feedback.action_type == 'convert':
                    true_label = 1
                elif feedback.action_type == 'contact' and feedback.contact_successful:
                    true_label = 1
                elif feedback.user_rating and feedback.user_rating >= 70:
                    true_label = 1
                else:
                    true_label = 0
                
                # Predicted label based on score
                pred_label = 1 if feedback.prediction_score and feedback.prediction_score >= 70 else 0
                
                y_true.append(true_label)
                y_pred.append(pred_label)
            
            # Calculate metrics
            from sklearn.metrics import f1_score, accuracy_score
            
            f1 = f1_score(y_true, y_pred, average='binary') if len(set(y_true)) > 1 else 0.0
            accuracy = accuracy_score(y_true, y_pred)
            
            return {
                'f1_score': f1,
                'accuracy': accuracy
            }
            
        except Exception as e:
            logger.error("Error calculating recent performance", error=str(e))
            return {'f1_score': 0.0, 'accuracy': 0.0}
    
    async def get_training_status(self, db: Session) -> Dict[str, Any]:
        """Get current training status and model information."""
        try:
            # Get current active model
            current_model = db.query(ModelMetrics).filter(
                ModelMetrics.is_active == True
            ).first()
            
            # Get total feedback count
            total_feedback = db.query(LeadFeedback).count()
            
            # Get recent feedback count
            recent_feedback = db.query(LeadFeedback).filter(
                LeadFeedback.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Check if retraining is needed
            retrain_check = await self.check_retraining_needed(db)
            
            return {
                'current_model': {
                    'version': current_model.model_version if current_model else None,
                    'created_at': current_model.created_at.isoformat() if current_model and current_model.created_at else None,
                    'f1_score': current_model.f1_score if current_model else None,
                    'is_active': current_model.is_active if current_model else False
                },
                'data_status': {
                    'total_feedback': total_feedback,
                    'recent_feedback': recent_feedback,
                    'min_training_samples': self.min_training_samples,
                    'sufficient_data': total_feedback >= self.min_training_samples
                },
                'retraining': retrain_check,
                'training_config': {
                    'min_training_samples': self.min_training_samples,
                    'min_feedback_samples': self.min_feedback_samples,
                    'retrain_threshold_f1': self.retrain_threshold_f1,
                    'retrain_interval_days': self.retrain_interval_days
                }
            }
            
        except Exception as e:
            logger.error("Error getting training status", error=str(e))
            return {
                'current_model': {'version': None, 'is_active': False},
                'data_status': {'total_feedback': 0, 'sufficient_data': False},
                'retraining': {'should_retrain': False, 'reasons': [f"Error: {str(e)}"]},
                'training_config': {}
            }
    
    async def cleanup_old_models(self, db: Session, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old model files and database records."""
        try:
            logger.info("Starting model cleanup", keep_count=keep_count)
            
            # Get all models ordered by creation date
            all_models = db.query(ModelMetrics).order_by(
                ModelMetrics.created_at.desc()
            ).all()
            
            if len(all_models) <= keep_count:
                return {
                    'success': True,
                    'message': f"Only {len(all_models)} models exist, no cleanup needed",
                    'deleted_count': 0
                }
            
            # Keep the most recent models and active models
            models_to_keep = all_models[:keep_count]
            active_models = [m for m in all_models if m.is_active]
            
            # Ensure we keep all active models
            keep_versions = set()
            for model in models_to_keep + active_models:
                keep_versions.add(model.model_version)
            
            # Delete old models
            deleted_count = 0
            for model in all_models:
                if model.model_version not in keep_versions:
                    # Delete model files
                    model_path = os.path.join(self.model_dir, f"model_{model.model_version}")
                    if os.path.exists(model_path):
                        import shutil
                        shutil.rmtree(model_path)
                        logger.info("Deleted model files", version=model.model_version)
                    
                    # Delete database record
                    db.delete(model)
                    deleted_count += 1
            
            db.commit()
            
            logger.info("Model cleanup completed", deleted_count=deleted_count)
            
            return {
                'success': True,
                'message': f"Cleaned up {deleted_count} old models",
                'deleted_count': deleted_count,
                'kept_count': len(keep_versions)
            }
            
        except Exception as e:
            logger.error("Error cleaning up models", error=str(e))
            return {
                'success': False,
                'message': f"Error during cleanup: {str(e)}",
                'deleted_count': 0
            }