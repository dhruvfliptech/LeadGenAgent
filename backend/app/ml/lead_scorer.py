"""
Lead scoring service using XGBoost with model versioning and A/B testing support.
"""

import os
import pickle
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import hashlib

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, accuracy_score
import mlflow
import mlflow.xgboost
import structlog
import joblib

from app.ml.feature_extractor import FeatureExtractor

logger = structlog.get_logger(__name__)


class LeadScorer:
    """XGBoost-based lead scoring system with model versioning."""
    
    def __init__(self, model_dir: str = "/tmp/models"):
        self.model_dir = model_dir
        self.feature_extractor = FeatureExtractor()
        self.model = None
        self.model_version = None
        self.model_metadata = {}
        self.is_loaded = False
        
        # Ensure model directory exists
        os.makedirs(model_dir, exist_ok=True)
        
        # XGBoost hyperparameters
        self.default_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        }
    
    def generate_model_version(self, features_hash: str, params_hash: str) -> str:
        """Generate a unique model version identifier."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        combined_hash = hashlib.md5(f"{features_hash}_{params_hash}".encode()).hexdigest()[:8]
        return f"v{timestamp}_{combined_hash}"
    
    def prepare_training_data(self, leads_data: List[Dict[str, Any]], 
                            feedback_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare training data from leads and feedback."""
        try:
            logger.info("Preparing training data", 
                       num_leads=len(leads_data), 
                       num_feedback=len(feedback_data))
            
            # Create feedback lookup
            feedback_lookup = {}
            for feedback in feedback_data:
                lead_id = feedback['lead_id']
                if lead_id not in feedback_lookup:
                    feedback_lookup[lead_id] = []
                feedback_lookup[lead_id].append(feedback)
            
            # Filter leads that have feedback
            leads_with_feedback = [
                lead for lead in leads_data 
                if lead['id'] in feedback_lookup
            ]
            
            if not leads_with_feedback:
                raise ValueError("No leads with feedback found for training")
            
            # Extract features
            features_df = self.feature_extractor.fit_transform(leads_with_feedback)
            
            # Create target labels
            targets = []
            for lead in leads_with_feedback:
                lead_id = lead['id']
                lead_feedback = feedback_lookup[lead_id]
                
                # Calculate target score based on feedback
                target_score = self._calculate_target_score(lead_feedback)
                targets.append(target_score)
            
            y = np.array(targets)
            
            # Remove lead_id column for training
            X = features_df.drop(['lead_id'], axis=1)
            
            logger.info("Training data prepared", 
                       num_features=X.shape[1], 
                       num_samples=X.shape[0],
                       positive_rate=np.mean(y))
            
            return X, y
            
        except Exception as e:
            logger.error("Error preparing training data", error=str(e))
            raise
    
    def _calculate_target_score(self, feedback_list: List[Dict[str, Any]]) -> float:
        """Calculate target score from feedback data."""
        """
        Target score calculation based on user actions:
        - Manual rating (0-100): Use directly if available
        - Contact + positive outcome: 0.8-1.0
        - Contact attempt: 0.6-0.8
        - Extended view time: 0.4-0.7
        - Quick archive: 0.0-0.3
        - View only: 0.3-0.5
        """
        
        max_score = 0.0
        
        for feedback in feedback_list:
            action_type = feedback.get('action_type', '')
            user_rating = feedback.get('user_rating')
            contact_successful = feedback.get('contact_successful')
            interaction_duration = feedback.get('interaction_duration', 0)
            conversion_value = feedback.get('conversion_value', 0)
            
            score = 0.0
            
            # Direct user rating takes precedence
            if user_rating is not None:
                score = user_rating / 100.0
            
            # Action-based scoring
            elif action_type == 'convert':
                score = 1.0
            elif action_type == 'contact':
                if contact_successful:
                    score = 0.9
                elif contact_successful is False:
                    score = 0.6
                else:
                    score = 0.7  # Contact attempted, outcome unknown
            elif action_type == 'archive':
                # Quick archive suggests low quality
                if interaction_duration and interaction_duration < 30:
                    score = 0.1
                else:
                    score = 0.3
            elif action_type == 'view':
                # Longer view times suggest higher interest
                if interaction_duration:
                    if interaction_duration > 300:  # 5+ minutes
                        score = 0.7
                    elif interaction_duration > 120:  # 2+ minutes
                        score = 0.5
                    elif interaction_duration > 30:  # 30+ seconds
                        score = 0.4
                    else:
                        score = 0.3
                else:
                    score = 0.4
            elif action_type == 'rate':
                if user_rating is not None:
                    score = user_rating / 100.0
                else:
                    score = 0.5
            
            # Boost score based on conversion value
            if conversion_value and conversion_value > 0:
                score = min(1.0, score + 0.2)
            
            max_score = max(max_score, score)
        
        return max_score
    
    def train(self, leads_data: List[Dict[str, Any]], 
              feedback_data: List[Dict[str, Any]],
              params: Optional[Dict] = None,
              validation_split: float = 0.2) -> Dict[str, Any]:
        """Train the XGBoost model."""
        try:
            start_time = datetime.utcnow()
            logger.info("Starting model training")
            
            # Prepare training data
            X, y = self.prepare_training_data(leads_data, feedback_data)
            
            # Split for validation
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Use provided params or defaults
            model_params = {**self.default_params, **(params or {})}
            
            # Generate model version
            features_hash = hashlib.md5(str(X.columns.tolist()).encode()).hexdigest()
            params_hash = hashlib.md5(str(model_params).encode()).hexdigest()
            self.model_version = self.generate_model_version(features_hash, params_hash)
            
            logger.info("Training XGBoost model", 
                       model_version=self.model_version,
                       train_samples=len(X_train),
                       val_samples=len(X_val))
            
            # Train model
            self.model = xgb.XGBClassifier(**model_params)
            
            eval_set = [(X_train, y_train), (X_val, y_val)]
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                eval_names=['train', 'val'],
                verbose=False,
                early_stopping_rounds=10
            )
            
            # Calculate metrics
            y_pred = self.model.predict(X_val)
            y_pred_proba = self.model.predict_proba(X_val)[:, 1]
            
            metrics = {
                'accuracy': accuracy_score(y_val, y_pred),
                'precision': precision_score(y_val, y_pred, average='binary'),
                'recall': recall_score(y_val, y_pred, average='binary'),
                'f1_score': f1_score(y_val, y_pred, average='binary'),
                'auc_roc': roc_auc_score(y_val, y_pred_proba),
                'training_samples': len(X_train),
                'validation_samples': len(X_val),
                'feature_count': X.shape[1],
                'training_duration': (datetime.utcnow() - start_time).total_seconds()
            }
            
            # Store model metadata
            self.model_metadata = {
                'version': self.model_version,
                'created_at': start_time.isoformat(),
                'features': X.columns.tolist(),
                'params': model_params,
                'metrics': metrics,
                'feature_extractor_fitted': True
            }
            
            # Save model
            self.save_model()
            
            self.is_loaded = True
            
            logger.info("Model training completed", 
                       model_version=self.model_version,
                       f1_score=metrics['f1_score'],
                       auc_roc=metrics['auc_roc'])
            
            return metrics
            
        except Exception as e:
            logger.error("Error training model", error=str(e))
            raise
    
    def predict_single(self, lead_data: Dict[str, Any], 
                      historical_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """Predict score for a single lead."""
        if not self.is_loaded:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            # Extract features
            features = self.feature_extractor.extract_features(lead_data, historical_stats)
            features_df = pd.DataFrame([features])
            
            # Remove lead_id if present
            if 'lead_id' in features_df.columns:
                features_df = features_df.drop(['lead_id'], axis=1)
            
            # Ensure feature order matches training
            expected_features = self.model_metadata.get('features', [])
            if expected_features:
                # Reorder and add missing features
                for feature in expected_features:
                    if feature not in features_df.columns:
                        features_df[feature] = 0
                features_df = features_df[expected_features]
            
            # Predict
            score_proba = self.model.predict_proba(features_df)[0, 1]
            score = int(score_proba * 100)  # Convert to 0-100 scale
            
            # Get feature importance for this prediction
            feature_importance = self._get_feature_importance(features_df.iloc[0])
            
            return {
                'score': score,
                'confidence': float(score_proba),
                'model_version': self.model_version,
                'feature_importance': feature_importance,
                'prediction_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error predicting single lead", 
                        lead_id=lead_data.get('id'), 
                        error=str(e))
            # Return default score to avoid pipeline failure
            return {
                'score': 50,
                'confidence': 0.5,
                'model_version': self.model_version,
                'feature_importance': {},
                'prediction_time': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def predict_batch(self, leads_data: List[Dict[str, Any]], 
                     historical_stats: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Predict scores for multiple leads."""
        if not self.is_loaded:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            logger.info("Predicting batch scores", num_leads=len(leads_data))
            
            # Extract features for all leads
            features_df = self.feature_extractor.transform(leads_data)
            lead_ids = features_df['lead_id'].tolist()
            features_df = features_df.drop(['lead_id'], axis=1)
            
            # Ensure feature order matches training
            expected_features = self.model_metadata.get('features', [])
            if expected_features:
                for feature in expected_features:
                    if feature not in features_df.columns:
                        features_df[feature] = 0
                features_df = features_df[expected_features]
            
            # Predict
            scores_proba = self.model.predict_proba(features_df)[:, 1]
            scores = (scores_proba * 100).astype(int)
            
            # Prepare results
            results = []
            for i, (lead_id, score, confidence) in enumerate(zip(lead_ids, scores, scores_proba)):
                results.append({
                    'lead_id': lead_id,
                    'score': int(score),
                    'confidence': float(confidence),
                    'model_version': self.model_version,
                    'prediction_time': datetime.utcnow().isoformat()
                })
            
            logger.info("Batch prediction completed", 
                       num_predictions=len(results),
                       avg_score=np.mean(scores))
            
            return results
            
        except Exception as e:
            logger.error("Error predicting batch", error=str(e))
            # Return default scores
            return [
                {
                    'lead_id': lead.get('id'),
                    'score': 50,
                    'confidence': 0.5,
                    'model_version': self.model_version,
                    'prediction_time': datetime.utcnow().isoformat(),
                    'error': str(e)
                }
                for lead in leads_data
            ]
    
    def _get_feature_importance(self, features: pd.Series) -> Dict[str, float]:
        """Get feature importance for interpretation."""
        try:
            if not hasattr(self.model, 'feature_importances_'):
                return {}
            
            # Get top 10 most important features
            importance_scores = self.model.feature_importances_
            feature_names = self.feature_extractor.get_feature_importance_names()
            
            if len(feature_names) != len(importance_scores):
                feature_names = [f'feature_{i}' for i in range(len(importance_scores))]
            
            # Sort by importance
            feature_importance = dict(zip(feature_names, importance_scores))
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            return dict(sorted_features[:10])
            
        except Exception as e:
            logger.error("Error calculating feature importance", error=str(e))
            return {}
    
    def save_model(self) -> str:
        """Save model and metadata to disk."""
        try:
            if not self.model or not self.model_version:
                raise ValueError("No model to save")
            
            model_path = os.path.join(self.model_dir, f"model_{self.model_version}")
            os.makedirs(model_path, exist_ok=True)
            
            # Save XGBoost model
            model_file = os.path.join(model_path, "model.pkl")
            joblib.dump(self.model, model_file)
            
            # Save feature extractor
            extractor_file = os.path.join(model_path, "feature_extractor.pkl")
            joblib.dump(self.feature_extractor, extractor_file)
            
            # Save metadata
            metadata_file = os.path.join(model_path, "metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
            
            logger.info("Model saved", 
                       model_version=self.model_version,
                       path=model_path)
            
            return model_path
            
        except Exception as e:
            logger.error("Error saving model", error=str(e))
            raise
    
    def load_model(self, model_version: Optional[str] = None) -> bool:
        """Load model from disk."""
        try:
            if model_version:
                self.model_version = model_version
            elif not self.model_version:
                # Load latest model
                self.model_version = self._get_latest_model_version()
            
            if not self.model_version:
                logger.warning("No model version specified or found")
                return False
            
            model_path = os.path.join(self.model_dir, f"model_{self.model_version}")
            
            if not os.path.exists(model_path):
                logger.error("Model path not found", path=model_path)
                return False
            
            # Load model
            model_file = os.path.join(model_path, "model.pkl")
            self.model = joblib.load(model_file)
            
            # Load feature extractor
            extractor_file = os.path.join(model_path, "feature_extractor.pkl")
            self.feature_extractor = joblib.load(extractor_file)
            
            # Load metadata
            metadata_file = os.path.join(model_path, "metadata.json")
            with open(metadata_file, 'r') as f:
                self.model_metadata = json.load(f)
            
            self.is_loaded = True
            
            logger.info("Model loaded successfully", 
                       model_version=self.model_version,
                       f1_score=self.model_metadata.get('metrics', {}).get('f1_score'))
            
            return True
            
        except Exception as e:
            logger.error("Error loading model", 
                        model_version=model_version, 
                        error=str(e))
            return False
    
    def _get_latest_model_version(self) -> Optional[str]:
        """Get the latest model version from disk."""
        try:
            if not os.path.exists(self.model_dir):
                return None
            
            model_dirs = [
                d for d in os.listdir(self.model_dir) 
                if d.startswith('model_v') and os.path.isdir(os.path.join(self.model_dir, d))
            ]
            
            if not model_dirs:
                return None
            
            # Sort by creation time
            model_dirs.sort(reverse=True)
            latest_dir = model_dirs[0]
            
            return latest_dir.replace('model_', '')
            
        except Exception as e:
            logger.error("Error getting latest model version", error=str(e))
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self.is_loaded:
            return {'error': 'No model loaded'}
        
        return {
            'version': self.model_version,
            'metadata': self.model_metadata,
            'is_loaded': self.is_loaded,
            'model_type': 'XGBoost',
            'feature_count': len(self.model_metadata.get('features', [])),
            'created_at': self.model_metadata.get('created_at'),
            'metrics': self.model_metadata.get('metrics', {})
        }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available model versions."""
        try:
            if not os.path.exists(self.model_dir):
                return []
            
            models = []
            for model_dir in os.listdir(self.model_dir):
                if model_dir.startswith('model_v'):
                    model_path = os.path.join(self.model_dir, model_dir)
                    metadata_file = os.path.join(model_path, "metadata.json")
                    
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            models.append({
                                'version': metadata.get('version'),
                                'created_at': metadata.get('created_at'),
                                'metrics': metadata.get('metrics', {}),
                                'feature_count': len(metadata.get('features', []))
                            })
                        except Exception as e:
                            logger.warning("Error reading model metadata", 
                                         model_dir=model_dir, 
                                         error=str(e))
            
            # Sort by creation time
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return models
            
        except Exception as e:
            logger.error("Error listing models", error=str(e))
            return []