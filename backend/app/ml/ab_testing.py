"""
A/B testing framework for comparing different ML models and scoring strategies.
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import structlog
import numpy as np
from scipy import stats

from app.models.feedback import ABTestVariant, LeadFeedback, ModelMetrics
from app.ml.lead_scorer import LeadScorer

logger = structlog.get_logger(__name__)


class ABTestStatus(Enum):
    """A/B test status enumeration."""
    PLANNED = "planned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTestManager:
    """Manages A/B testing for ML models."""
    
    def __init__(self):
        self.active_tests = {}  # Cache for active tests
        self.model_cache = {}   # Cache for loaded models
        
        # Statistical significance thresholds
        self.min_sample_size = 100
        self.significance_level = 0.05
        self.min_effect_size = 0.02  # 2% minimum difference
        
    async def create_ab_test(self, db: Session, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B test configuration."""
        try:
            test_name = test_config['test_name']
            variants = test_config['variants']  # List of variant configurations
            
            logger.info("Creating A/B test", test_name=test_name, variants_count=len(variants))
            
            # Validate test configuration
            if not test_name or not variants:
                raise ValueError("Test name and variants are required")
            
            if len(variants) < 2:
                raise ValueError("At least 2 variants are required for A/B test")
            
            # Check for existing test with same name
            existing_test = db.query(ABTestVariant).filter(
                ABTestVariant.test_name == test_name,
                ABTestVariant.is_active == True
            ).first()
            
            if existing_test:
                raise ValueError(f"Active test with name '{test_name}' already exists")
            
            # Validate traffic allocation
            total_traffic = sum(v.get('traffic_percentage', 0) for v in variants)
            if abs(total_traffic - 100.0) > 0.01:
                raise ValueError(f"Traffic allocation must sum to 100%, got {total_traffic}%")
            
            # Create variant records
            created_variants = []
            start_date = datetime.utcnow()
            
            for i, variant_config in enumerate(variants):
                variant = ABTestVariant(
                    test_name=test_name,
                    variant_name=variant_config['variant_name'],
                    model_version=variant_config['model_version'],
                    traffic_percentage=variant_config['traffic_percentage'],
                    is_control=variant_config.get('is_control', i == 0),
                    is_active=True,
                    start_date=start_date
                )
                
                db.add(variant)
                created_variants.append(variant)
            
            db.commit()
            
            # Load test into cache
            await self._load_test_cache(db, test_name)
            
            logger.info("A/B test created successfully", 
                       test_name=test_name,
                       variants=[v.variant_name for v in created_variants])
            
            return {
                'success': True,
                'test_name': test_name,
                'variants': [
                    {
                        'variant_name': v.variant_name,
                        'model_version': v.model_version,
                        'traffic_percentage': v.traffic_percentage,
                        'is_control': v.is_control
                    }
                    for v in created_variants
                ],
                'start_date': start_date.isoformat(),
                'message': 'A/B test created successfully'
            }
            
        except Exception as e:
            logger.error("Error creating A/B test", 
                        test_name=test_config.get('test_name'),
                        error=str(e))
            db.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create A/B test'
            }
    
    async def assign_variant(self, db: Session, test_name: str, 
                           user_id: Optional[str] = None) -> Dict[str, Any]:
        """Assign a user to an A/B test variant."""
        try:
            # Check if test is cached
            if test_name not in self.active_tests:
                await self._load_test_cache(db, test_name)
            
            if test_name not in self.active_tests:
                return {
                    'success': False,
                    'error': f'Test {test_name} not found or not active',
                    'variant': None
                }
            
            test_variants = self.active_tests[test_name]
            
            # Determine variant based on consistent hashing or random assignment
            if user_id:
                # Consistent assignment based on user_id hash
                hash_value = int(hashlib.md5(f"{test_name}_{user_id}".encode()).hexdigest(), 16)
                assignment_value = (hash_value % 10000) / 100.0  # 0-100
            else:
                # Random assignment
                assignment_value = random.uniform(0, 100)
            
            # Find appropriate variant based on traffic allocation
            cumulative_traffic = 0
            assigned_variant = None
            
            for variant in test_variants:
                cumulative_traffic += variant['traffic_percentage']
                if assignment_value <= cumulative_traffic:
                    assigned_variant = variant
                    break
            
            if not assigned_variant:
                # Fallback to last variant
                assigned_variant = test_variants[-1]
            
            logger.debug("Variant assigned", 
                        test_name=test_name,
                        variant=assigned_variant['variant_name'],
                        user_id=user_id)
            
            return {
                'success': True,
                'test_name': test_name,
                'variant_name': assigned_variant['variant_name'],
                'model_version': assigned_variant['model_version'],
                'is_control': assigned_variant['is_control'],
                'traffic_percentage': assigned_variant['traffic_percentage']
            }
            
        except Exception as e:
            logger.error("Error assigning variant", 
                        test_name=test_name,
                        error=str(e))
            return {
                'success': False,
                'error': str(e),
                'variant': None
            }
    
    async def score_with_ab_test(self, db: Session, test_name: str, 
                               lead_data: Dict[str, Any],
                               user_id: Optional[str] = None) -> Dict[str, Any]:
        """Score a lead using A/B test variant assignment."""
        try:
            # Assign variant
            variant_assignment = await self.assign_variant(db, test_name, user_id)
            
            if not variant_assignment['success']:
                # Fall back to default scoring
                default_scorer = LeadScorer()
                if not default_scorer.load_model():
                    raise ValueError("No model available for scoring")
                
                prediction = default_scorer.predict_single(lead_data)
                prediction['ab_test_variant'] = None
                prediction['ab_test_error'] = variant_assignment.get('error')
                
                return prediction
            
            # Get model for assigned variant
            model_version = variant_assignment['model_version']
            
            # Load model if not cached
            if model_version not in self.model_cache:
                scorer = LeadScorer()
                success = scorer.load_model(model_version)
                if not success:
                    raise ValueError(f"Failed to load model {model_version}")
                self.model_cache[model_version] = scorer
            
            scorer = self.model_cache[model_version]
            
            # Get prediction
            prediction = scorer.predict_single(lead_data)
            
            # Add A/B test metadata
            prediction['ab_test_name'] = test_name
            prediction['ab_test_variant'] = variant_assignment['variant_name']
            prediction['is_control'] = variant_assignment['is_control']
            
            # Record assignment for analysis
            await self._record_test_assignment(
                db, test_name, variant_assignment['variant_name'],
                lead_data.get('id'), prediction['score']
            )
            
            return prediction
            
        except Exception as e:
            logger.error("Error scoring with A/B test", 
                        test_name=test_name,
                        lead_id=lead_data.get('id'),
                        error=str(e))
            raise
    
    async def analyze_test_results(self, db: Session, test_name: str) -> Dict[str, Any]:
        """Analyze A/B test results and statistical significance."""
        try:
            logger.info("Analyzing A/B test results", test_name=test_name)
            
            # Get test variants
            variants = db.query(ABTestVariant).filter(
                ABTestVariant.test_name == test_name
            ).all()
            
            if not variants:
                return {
                    'success': False,
                    'error': f'Test {test_name} not found',
                    'results': {}
                }
            
            # Get feedback data for each variant
            variant_results = {}
            
            for variant in variants:
                # Get feedback for this variant's model version
                feedback_data = db.query(LeadFeedback).filter(
                    LeadFeedback.model_version == variant.model_version,
                    LeadFeedback.created_at >= variant.start_date
                ).all()
                
                if variant.end_date:
                    feedback_data = [f for f in feedback_data if f.created_at <= variant.end_date]
                
                # Calculate metrics
                metrics = self._calculate_variant_metrics(feedback_data)
                
                variant_results[variant.variant_name] = {
                    'variant_name': variant.variant_name,
                    'model_version': variant.model_version,
                    'is_control': variant.is_control,
                    'traffic_percentage': variant.traffic_percentage,
                    'sample_size': len(feedback_data),
                    'metrics': metrics
                }
            
            # Perform statistical tests
            statistical_results = self._perform_statistical_tests(variant_results)
            
            # Update variant records with results
            for variant_name, results in variant_results.items():
                variant = next(v for v in variants if v.variant_name == variant_name)
                variant.sample_size = results['sample_size']
                variant.conversion_rate = results['metrics'].get('conversion_rate', 0)
                variant.avg_score = results['metrics'].get('avg_score', 0)
                
                # Add confidence intervals and significance
                if variant_name in statistical_results:
                    stat_result = statistical_results[variant_name]
                    variant.confidence_interval_lower = stat_result.get('ci_lower')
                    variant.confidence_interval_upper = stat_result.get('ci_upper')
                    variant.statistical_significance = stat_result.get('p_value')
            
            db.commit()
            
            return {
                'success': True,
                'test_name': test_name,
                'start_date': min(v.start_date for v in variants).isoformat(),
                'end_date': max(v.end_date for v in variants if v.end_date),
                'variant_results': variant_results,
                'statistical_analysis': statistical_results,
                'recommendations': self._generate_recommendations(variant_results, statistical_results)
            }
            
        except Exception as e:
            logger.error("Error analyzing test results", 
                        test_name=test_name,
                        error=str(e))
            return {
                'success': False,
                'error': str(e),
                'results': {}
            }
    
    async def stop_test(self, db: Session, test_name: str, 
                       winner_variant: Optional[str] = None) -> Dict[str, Any]:
        """Stop an A/B test and optionally declare a winner."""
        try:
            logger.info("Stopping A/B test", 
                       test_name=test_name,
                       winner=winner_variant)
            
            # Get test variants
            variants = db.query(ABTestVariant).filter(
                ABTestVariant.test_name == test_name,
                ABTestVariant.is_active == True
            ).all()
            
            if not variants:
                return {
                    'success': False,
                    'error': f'Active test {test_name} not found',
                    'message': 'Test not found or already stopped'
                }
            
            # Set end date and deactivate
            end_date = datetime.utcnow()
            
            for variant in variants:
                variant.is_active = False
                variant.end_date = end_date
            
            # If winner is specified, activate that model version
            if winner_variant:
                winner = next((v for v in variants if v.variant_name == winner_variant), None)
                if not winner:
                    return {
                        'success': False,
                        'error': f'Winner variant {winner_variant} not found in test',
                        'message': 'Invalid winner variant'
                    }
                
                # Deactivate all current models and activate winner
                db.query(ModelMetrics).update({'is_active': False})
                
                winner_model = db.query(ModelMetrics).filter(
                    ModelMetrics.model_version == winner.model_version
                ).first()
                
                if winner_model:
                    winner_model.is_active = True
                    winner_model.deployed_at = datetime.utcnow()
            
            db.commit()
            
            # Remove from cache
            if test_name in self.active_tests:
                del self.active_tests[test_name]
            
            # Get final analysis
            final_analysis = await self.analyze_test_results(db, test_name)
            
            logger.info("A/B test stopped successfully", 
                       test_name=test_name,
                       winner=winner_variant)
            
            return {
                'success': True,
                'test_name': test_name,
                'end_date': end_date.isoformat(),
                'winner_variant': winner_variant,
                'final_analysis': final_analysis,
                'message': 'Test stopped successfully'
            }
            
        except Exception as e:
            logger.error("Error stopping A/B test", 
                        test_name=test_name,
                        error=str(e))
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to stop test'
            }
    
    async def get_active_tests(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active A/B tests."""
        try:
            active_tests = db.query(ABTestVariant).filter(
                ABTestVariant.is_active == True
            ).all()
            
            # Group by test name
            tests_by_name = {}
            for variant in active_tests:
                test_name = variant.test_name
                if test_name not in tests_by_name:
                    tests_by_name[test_name] = []
                tests_by_name[test_name].append(variant)
            
            # Format results
            test_list = []
            for test_name, variants in tests_by_name.items():
                test_info = {
                    'test_name': test_name,
                    'start_date': min(v.start_date for v in variants).isoformat(),
                    'variant_count': len(variants),
                    'variants': [
                        {
                            'variant_name': v.variant_name,
                            'model_version': v.model_version,
                            'traffic_percentage': v.traffic_percentage,
                            'is_control': v.is_control,
                            'sample_size': v.sample_size
                        }
                        for v in variants
                    ],
                    'total_sample_size': sum(v.sample_size or 0 for v in variants)
                }
                test_list.append(test_info)
            
            return test_list
            
        except Exception as e:
            logger.error("Error getting active tests", error=str(e))
            return []
    
    def _calculate_variant_metrics(self, feedback_data: List[LeadFeedback]) -> Dict[str, float]:
        """Calculate performance metrics for a variant."""
        if not feedback_data:
            return {
                'conversion_rate': 0.0,
                'contact_success_rate': 0.0,
                'avg_score': 0.0,
                'avg_interaction_time': 0.0
            }
        
        # Conversion rate
        conversions = [f for f in feedback_data if f.action_type == 'convert']
        conversion_rate = len(conversions) / len(feedback_data)
        
        # Contact success rate
        contacts = [f for f in feedback_data if f.action_type == 'contact']
        successful_contacts = [f for f in contacts if f.contact_successful]
        contact_success_rate = len(successful_contacts) / len(contacts) if contacts else 0.0
        
        # Average prediction score
        scores = [f.prediction_score for f in feedback_data if f.prediction_score is not None]
        avg_score = np.mean(scores) if scores else 0.0
        
        # Average interaction time
        interaction_times = [f.interaction_duration for f in feedback_data if f.interaction_duration]
        avg_interaction_time = np.mean(interaction_times) if interaction_times else 0.0
        
        return {
            'conversion_rate': conversion_rate,
            'contact_success_rate': contact_success_rate,
            'avg_score': avg_score,
            'avg_interaction_time': avg_interaction_time,
            'total_conversions': len(conversions),
            'total_contacts': len(contacts),
            'successful_contacts': len(successful_contacts)
        }
    
    def _perform_statistical_tests(self, variant_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical significance tests between variants."""
        results = {}
        
        try:
            # Find control variant
            control_variant = None
            for variant_name, results_data in variant_results.items():
                if results_data['is_control']:
                    control_variant = variant_name
                    break
            
            if not control_variant:
                # No control specified, use first variant
                control_variant = next(iter(variant_results.keys()))
            
            control_data = variant_results[control_variant]
            
            # Compare each variant to control
            for variant_name, variant_data in variant_results.items():
                if variant_name == control_variant:
                    results[variant_name] = {
                        'is_control': True,
                        'p_value': None,
                        'effect_size': 0.0,
                        'significant': False,
                        'ci_lower': None,
                        'ci_upper': None
                    }
                    continue
                
                # Perform two-proportion z-test for conversion rates
                control_conversions = control_data['metrics']['total_conversions']
                control_sample = control_data['sample_size']
                variant_conversions = variant_data['metrics']['total_conversions']
                variant_sample = variant_data['sample_size']
                
                if control_sample >= self.min_sample_size and variant_sample >= self.min_sample_size:
                    # Two-proportion z-test
                    p1 = control_conversions / control_sample
                    p2 = variant_conversions / variant_sample
                    
                    n1, n2 = control_sample, variant_sample
                    pooled_p = (control_conversions + variant_conversions) / (n1 + n2)
                    
                    if pooled_p > 0 and pooled_p < 1:
                        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
                        z_score = (p2 - p1) / se
                        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                        
                        # Calculate confidence interval for difference
                        diff = p2 - p1
                        se_diff = np.sqrt((p1*(1-p1)/n1) + (p2*(1-p2)/n2))
                        ci_margin = 1.96 * se_diff  # 95% CI
                        
                        results[variant_name] = {
                            'is_control': False,
                            'p_value': p_value,
                            'effect_size': diff,
                            'significant': p_value < self.significance_level and abs(diff) > self.min_effect_size,
                            'ci_lower': diff - ci_margin,
                            'ci_upper': diff + ci_margin,
                            'z_score': z_score
                        }
                    else:
                        # Edge case: no conversions
                        results[variant_name] = {
                            'is_control': False,
                            'p_value': 1.0,
                            'effect_size': 0.0,
                            'significant': False,
                            'ci_lower': None,
                            'ci_upper': None
                        }
                else:
                    # Insufficient sample size
                    results[variant_name] = {
                        'is_control': False,
                        'p_value': None,
                        'effect_size': None,
                        'significant': False,
                        'insufficient_sample': True,
                        'ci_lower': None,
                        'ci_upper': None
                    }
            
            return results
            
        except Exception as e:
            logger.error("Error performing statistical tests", error=str(e))
            return {}
    
    def _generate_recommendations(self, variant_results: Dict[str, Any], 
                                statistical_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        try:
            # Find best performing variant
            best_variant = max(
                variant_results.items(),
                key=lambda x: x[1]['metrics']['conversion_rate']
            )
            
            best_name = best_variant[0]
            best_conversion_rate = best_variant[1]['metrics']['conversion_rate']
            
            # Check if winner has sufficient sample size
            if best_variant[1]['sample_size'] < self.min_sample_size:
                recommendations.append(
                    f"Insufficient sample size for {best_name}. "
                    f"Collect at least {self.min_sample_size} samples before making decisions."
                )
            
            # Check statistical significance
            if best_name in statistical_results:
                stat_result = statistical_results[best_name]
                if stat_result.get('significant'):
                    effect_size = stat_result['effect_size']
                    recommendations.append(
                        f"✅ {best_name} shows statistically significant improvement "
                        f"(+{effect_size:.1%} conversion rate). Recommend implementing this variant."
                    )
                elif stat_result.get('p_value') and stat_result['p_value'] > 0.05:
                    recommendations.append(
                        f"⚠️ {best_name} shows higher conversion rate but not statistically significant "
                        f"(p={stat_result['p_value']:.3f}). Consider running test longer."
                    )
            
            # Check for clear winner
            conversion_rates = [v['metrics']['conversion_rate'] for v in variant_results.values()]
            if max(conversion_rates) - min(conversion_rates) < 0.01:  # Less than 1% difference
                recommendations.append(
                    "🔄 Variants show similar performance. "
                    "Consider testing more distinct variations or running longer."
                )
            
            # Sample size recommendations
            total_samples = sum(v['sample_size'] for v in variant_results.values())
            if total_samples < self.min_sample_size * len(variant_results):
                recommendations.append(
                    f"📊 Total sample size ({total_samples}) is low. "
                    f"Target at least {self.min_sample_size * len(variant_results)} total samples."
                )
            
        except Exception as e:
            logger.error("Error generating recommendations", error=str(e))
            recommendations.append("⚠️ Error generating recommendations. Review results manually.")
        
        return recommendations
    
    async def _load_test_cache(self, db: Session, test_name: str):
        """Load test configuration into cache."""
        try:
            variants = db.query(ABTestVariant).filter(
                ABTestVariant.test_name == test_name,
                ABTestVariant.is_active == True
            ).all()
            
            if variants:
                self.active_tests[test_name] = [
                    {
                        'variant_name': v.variant_name,
                        'model_version': v.model_version,
                        'traffic_percentage': v.traffic_percentage,
                        'is_control': v.is_control
                    }
                    for v in variants
                ]
                
                logger.debug("Test loaded into cache", 
                           test_name=test_name,
                           variants_count=len(variants))
        
        except Exception as e:
            logger.error("Error loading test cache", 
                        test_name=test_name,
                        error=str(e))
    
    async def _record_test_assignment(self, db: Session, test_name: str, 
                                    variant_name: str, lead_id: Optional[int],
                                    score: float):
        """Record test assignment for analysis (optional tracking)."""
        try:
            # This could store assignment data in a separate table
            # For now, we rely on the model_version in feedback records
            logger.debug("Test assignment recorded", 
                        test_name=test_name,
                        variant=variant_name,
                        lead_id=lead_id,
                        score=score)
        
        except Exception as e:
            logger.warning("Error recording test assignment", error=str(e))