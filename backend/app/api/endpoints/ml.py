"""
ML API endpoints for lead scoring, feedback processing, and model management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db, engine
from app.models.leads import Lead
from app.models.feedback import LeadFeedback, ModelMetrics
from app.ml.lead_scorer import LeadScorer
from app.ml.model_trainer import ModelTrainer
from app.ml.feedback_processor import FeedbackProcessor
from app.ml.ab_testing import ABTestManager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["machine-learning"])

# Global instances
scorer = LeadScorer()
trainer = ModelTrainer()
feedback_processor = FeedbackProcessor()
ab_test_manager = ABTestManager()


# Pydantic models for request/response
class LeadScoreRequest(BaseModel):
    lead_id: int
    title: str
    description: Optional[str] = ""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    location_name: Optional[str] = None
    posted_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class BatchScoreRequest(BaseModel):
    leads: List[LeadScoreRequest]


class FeedbackRequest(BaseModel):
    lead_id: int
    action_type: str = Field(..., pattern="^(view|contact|archive|rate|convert)$")
    user_rating: Optional[float] = Field(None, ge=0, le=100)
    interaction_duration: Optional[float] = None  # seconds
    contact_successful: Optional[bool] = None
    contact_response_time: Optional[float] = None  # hours
    conversion_value: Optional[float] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class ImplicitFeedbackRequest(BaseModel):
    session_id: str
    interactions: List[Dict[str, Any]]


class ModelTrainRequest(BaseModel):
    force_retrain: bool = False
    validation_split: float = Field(0.2, ge=0.1, le=0.5)
    params: Optional[Dict[str, Any]] = None


class ScoreResponse(BaseModel):
    lead_id: int
    score: int
    confidence: float
    model_version: str
    feature_importance: Dict[str, float]
    prediction_time: str


class BatchScoreResponse(BaseModel):
    predictions: List[ScoreResponse]
    total_count: int
    avg_score: float
    processing_time: str


class FeedbackResponse(BaseModel):
    success: bool
    feedback_id: Optional[int] = None
    confidence: float
    prediction_score: Optional[float] = None
    message: str


class ModelMetricsResponse(BaseModel):
    current_model: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_status: Dict[str, Any]
    feedback_analytics: Dict[str, Any]


class ABTestVariantConfig(BaseModel):
    variant_name: str
    model_version: str
    traffic_percentage: float = Field(..., ge=0, le=100)
    is_control: bool = False


class ABTestCreateRequest(BaseModel):
    test_name: str
    variants: List[ABTestVariantConfig]


class ABTestScoreRequest(BaseModel):
    test_name: str
    lead_data: LeadScoreRequest
    user_id: Optional[str] = None


# Initialize model on startup
@router.on_event("startup")
async def load_model():
    """Load the latest model on startup."""
    try:
        success = scorer.load_model()
        if success:
            logger.info("Model loaded successfully on startup", 
                       version=scorer.model_version)
        else:
            logger.warning("No model found on startup - will need training")
    except Exception as e:
        logger.error("Error loading model on startup", error=str(e))


@router.post("/score", response_model=ScoreResponse)
async def score_lead(request: LeadScoreRequest, db: Session = Depends(get_db)):
    """Score a single lead using the current ML model."""
    try:
        # Check if model is loaded
        if not scorer.is_loaded:
            # Try to load the latest model
            if not scorer.load_model():
                raise HTTPException(
                    status_code=503,
                    detail="ML model not available. Please train a model first."
                )
        
        # Convert request to dict for processing
        lead_data = request.dict()
        
        # Get historical stats for this lead (optional enhancement)
        historical_stats = None  # Could implement historical performance lookup
        
        # Get prediction
        prediction = scorer.predict_single(lead_data, historical_stats)
        
        # Store prediction in database for tracking
        await _store_prediction(db, request.lead_id, prediction)
        
        return ScoreResponse(
            lead_id=request.lead_id,
            score=prediction['score'],
            confidence=prediction['confidence'],
            model_version=prediction['model_version'],
            feature_importance=prediction.get('feature_importance', {}),
            prediction_time=prediction['prediction_time']
        )
        
    except Exception as e:
        logger.error("Error scoring lead", 
                    lead_id=request.lead_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@router.post("/batch-score", response_model=BatchScoreResponse)
async def batch_score_leads(request: BatchScoreRequest, db: Session = Depends(get_db)):
    """Score multiple leads in batch."""
    try:
        start_time = datetime.utcnow()
        
        # Check if model is loaded
        if not scorer.is_loaded:
            if not scorer.load_model():
                raise HTTPException(
                    status_code=503,
                    detail="ML model not available. Please train a model first."
                )
        
        # Convert requests to list of dicts
        leads_data = [lead.dict() for lead in request.leads]
        
        # Get batch predictions
        predictions = scorer.predict_batch(leads_data)
        
        # Convert to response format
        score_responses = []
        total_score = 0
        
        for pred in predictions:
            score_response = ScoreResponse(
                lead_id=pred['lead_id'],
                score=pred['score'],
                confidence=pred['confidence'],
                model_version=pred['model_version'],
                feature_importance={},  # Not included in batch for performance
                prediction_time=pred['prediction_time']
            )
            score_responses.append(score_response)
            total_score += pred['score']
        
        # Store batch predictions
        await _store_batch_predictions(db, predictions)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        avg_score = total_score / len(predictions) if predictions else 0
        
        return BatchScoreResponse(
            predictions=score_responses,
            total_count=len(predictions),
            avg_score=avg_score,
            processing_time=f"{processing_time:.2f}s"
        )
        
    except Exception as e:
        logger.error("Error batch scoring leads", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch scoring error: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Record user feedback on a lead."""
    try:
        # Convert request to dict
        feedback_data = request.dict()
        
        # Process feedback
        result = await feedback_processor.process_user_feedback(db, feedback_data)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Feedback processing failed'))
        
        return FeedbackResponse(
            success=True,
            feedback_id=result['feedback_id'],
            confidence=result['confidence'],
            prediction_score=result.get('prediction_score'),
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error recording feedback", 
                    lead_id=request.lead_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@router.post("/feedback/implicit")
async def record_implicit_feedback(request: ImplicitFeedbackRequest, db: Session = Depends(get_db)):
    """Record implicit feedback from user interactions."""
    try:
        feedback_data = request.dict()
        results = await feedback_processor.generate_implicit_feedback(db, feedback_data)
        
        return {
            "success": True,
            "feedback_count": len(results),
            "feedback_records": results,
            "message": f"Generated {len(results)} implicit feedback records"
        }
        
    except Exception as e:
        logger.error("Error recording implicit feedback", error=str(e))
        raise HTTPException(status_code=500, detail=f"Implicit feedback error: {str(e)}")


@router.post("/feedback/batch")
async def record_batch_feedback(feedback_batch: List[FeedbackRequest], db: Session = Depends(get_db)):
    """Record multiple feedback records in batch."""
    try:
        feedback_data = [fb.dict() for fb in feedback_batch]
        result = await feedback_processor.bulk_process_feedback(db, feedback_data)
        
        return result
        
    except Exception as e:
        logger.error("Error recording batch feedback", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch feedback error: {str(e)}")


@router.get("/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(db: Session = Depends(get_db)):
    """Get current model performance metrics and analytics."""
    try:
        # Get current model info
        model_info = scorer.get_model_info()
        
        # Get training status
        training_status = await trainer.get_training_status(db)
        
        # Get feedback analytics
        feedback_analytics = await feedback_processor.get_feedback_analytics(db)
        
        # Get performance metrics from database
        current_metrics = db.query(ModelMetrics).filter(
            ModelMetrics.is_active == True
        ).first()
        
        performance_metrics = {}
        if current_metrics:
            performance_metrics = {
                'precision': current_metrics.precision,
                'recall': current_metrics.recall,
                'f1_score': current_metrics.f1_score,
                'auc_roc': current_metrics.auc_roc,
                'accuracy': current_metrics.accuracy,
                'conversion_rate': current_metrics.conversion_rate,
                'contact_success_rate': current_metrics.contact_success_rate
            }
        
        return ModelMetricsResponse(
            current_model=model_info,
            performance_metrics=performance_metrics,
            training_status=training_status,
            feedback_analytics=feedback_analytics
        )
        
    except Exception as e:
        logger.error("Error getting model metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")


@router.post("/retrain")
async def retrain_model(request: ModelTrainRequest, 
                       background_tasks: BackgroundTasks,
                       db: Session = Depends(get_db)):
    """Trigger model retraining."""
    try:
        logger.info("Model retraining requested", force=request.force_retrain)
        
        # Start retraining in background
        background_tasks.add_task(
            _retrain_model_task,
            db,
            request.force_retrain,
            request.validation_split,
            request.params
        )
        
        return {
            "success": True,
            "message": "Model retraining started in background",
            "force_retrain": request.force_retrain,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error starting model retraining", error=str(e))
        raise HTTPException(status_code=500, detail=f"Retraining error: {str(e)}")


@router.get("/models")
async def list_models():
    """List all available model versions."""
    try:
        models = scorer.list_available_models()
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        logger.error("Error listing models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Model listing error: {str(e)}")


@router.post("/models/{model_version}/activate")
async def activate_model(model_version: str, db: Session = Depends(get_db)):
    """Activate a specific model version."""
    try:
        # Load the specified model
        success = scorer.load_model(model_version)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Model version {model_version} not found")
        
        # Update database to mark this model as active
        db.query(ModelMetrics).update({'is_active': False})  # Deactivate all
        
        model_metrics = db.query(ModelMetrics).filter(
            ModelMetrics.model_version == model_version
        ).first()
        
        if model_metrics:
            model_metrics.is_active = True
            model_metrics.deployed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info("Model activated", version=model_version)
        
        return {
            "success": True,
            "message": f"Model {model_version} activated successfully",
            "active_model": scorer.get_model_info()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error activating model", 
                    version=model_version,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Model activation error: {str(e)}")


@router.get("/feedback/{lead_id}")
async def get_lead_feedback(lead_id: int, db: Session = Depends(get_db)):
    """Get feedback history for a specific lead."""
    try:
        feedback_history = await feedback_processor.get_lead_feedback_history(db, lead_id)
        
        return {
            "success": True,
            "lead_id": lead_id,
            "feedback_count": len(feedback_history),
            "feedback_history": feedback_history
        }
        
    except Exception as e:
        logger.error("Error getting lead feedback", 
                    lead_id=lead_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Feedback retrieval error: {str(e)}")


@router.get("/analytics/feedback")
async def get_feedback_analytics(days: int = 7, db: Session = Depends(get_db)):
    """Get feedback analytics for specified number of days."""
    try:
        analytics = await feedback_processor.get_feedback_analytics(db, days)
        return analytics
        
    except Exception as e:
        logger.error("Error getting feedback analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.post("/cleanup/models")
async def cleanup_old_models(keep_count: int = 5, db: Session = Depends(get_db)):
    """Clean up old model files and records."""
    try:
        result = await trainer.cleanup_old_models(db, keep_count)
        return result
        
    except Exception as e:
        logger.error("Error cleaning up models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")


@router.post("/cleanup/feedback")
async def cleanup_old_feedback(retention_days: int = 365, db: Session = Depends(get_db)):
    """Clean up old feedback records."""
    try:
        result = await feedback_processor.cleanup_old_feedback(db, retention_days)
        return result
        
    except Exception as e:
        logger.error("Error cleaning up feedback", error=str(e))
        raise HTTPException(status_code=500, detail=f"Feedback cleanup error: {str(e)}")


# Helper functions
async def _store_prediction(db: Session, lead_id: int, prediction: Dict[str, Any]):
    """Store prediction result for tracking."""
    try:
        # Update any existing feedback records with the prediction
        db.query(LeadFeedback).filter(
            LeadFeedback.lead_id == lead_id,
            LeadFeedback.prediction_score.is_(None)
        ).update({
            'prediction_score': prediction['score'],
            'model_version': prediction['model_version']
        })
        
        db.commit()
        
    except Exception as e:
        logger.warning("Error storing prediction", 
                      lead_id=lead_id,
                      error=str(e))


async def _store_batch_predictions(db: Session, predictions: List[Dict[str, Any]]):
    """Store batch predictions for tracking."""
    try:
        # This could be optimized with bulk updates
        for pred in predictions:
            await _store_prediction(db, pred['lead_id'], pred)
        
    except Exception as e:
        logger.warning("Error storing batch predictions", error=str(e))


async def _retrain_model_task(db: Session, force_retrain: bool, 
                            validation_split: float, params: Optional[Dict]):
    """Background task for model retraining."""
    try:
        logger.info("Starting background model retraining")
        
        result = await trainer.retrain_model(db, force=force_retrain)
        
        if result['success'] and result['retrained']:
            # Reload the new model
            new_version = result['training_results']['model_version']
            success = scorer.load_model(new_version)
            
            if success:
                logger.info("New model loaded after retraining", version=new_version)
            else:
                logger.error("Failed to load new model after retraining")
        
        logger.info("Background retraining completed", 
                   success=result['success'],
                   retrained=result['retrained'])
        
    except Exception as e:
        logger.error("Error in background retraining task", error=str(e))


# A/B Testing Endpoints
@router.post("/ab-tests")
async def create_ab_test(request: ABTestCreateRequest, db: Session = Depends(get_db)):
    """Create a new A/B test for model comparison."""
    try:
        test_config = request.dict()
        result = await ab_test_manager.create_ab_test(db, test_config)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating A/B test", error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test creation error: {str(e)}")


@router.get("/ab-tests")
async def list_ab_tests(db: Session = Depends(get_db)):
    """List all active A/B tests."""
    try:
        tests = await ab_test_manager.get_active_tests(db)
        return {
            "success": True,
            "active_tests": tests,
            "count": len(tests)
        }
        
    except Exception as e:
        logger.error("Error listing A/B tests", error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test listing error: {str(e)}")


@router.post("/ab-tests/{test_name}/score")
async def score_with_ab_test(test_name: str, request: ABTestScoreRequest, db: Session = Depends(get_db)):
    """Score a lead using A/B test variant assignment."""
    try:
        lead_data = request.lead_data.dict()
        prediction = await ab_test_manager.score_with_ab_test(
            db, test_name, lead_data, request.user_id
        )
        
        return prediction
        
    except Exception as e:
        logger.error("Error scoring with A/B test", 
                    test_name=test_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test scoring error: {str(e)}")


@router.get("/ab-tests/{test_name}/results")
async def get_ab_test_results(test_name: str, db: Session = Depends(get_db)):
    """Get A/B test results and statistical analysis."""
    try:
        results = await ab_test_manager.analyze_test_results(db, test_name)
        
        if not results['success']:
            raise HTTPException(status_code=404, detail=results['error'])
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting A/B test results", 
                    test_name=test_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test results error: {str(e)}")


@router.post("/ab-tests/{test_name}/stop")
async def stop_ab_test(test_name: str, winner_variant: Optional[str] = None, db: Session = Depends(get_db)):
    """Stop an A/B test and optionally declare a winner."""
    try:
        result = await ab_test_manager.stop_test(db, test_name, winner_variant)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error stopping A/B test", 
                    test_name=test_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test stop error: {str(e)}")


@router.get("/ab-tests/{test_name}/assign")
async def assign_ab_test_variant(test_name: str, user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Assign a user to an A/B test variant."""
    try:
        assignment = await ab_test_manager.assign_variant(db, test_name, user_id)
        
        if not assignment['success']:
            raise HTTPException(status_code=404, detail=assignment['error'])
        
        return assignment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error assigning A/B test variant", 
                    test_name=test_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"A/B test assignment error: {str(e)}")


@router.get("/health")
async def ml_health_check(db = Depends(get_db)):
    """Health check endpoint for ML services."""
    try:
        # Check model availability
        model_status = {
            "model_loaded": scorer.is_loaded,
            "model_version": scorer.model_version if scorer.is_loaded else None
        }
        
        # Check database connectivity using async engine
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = {"status": "connected"}
        except Exception as e:
            db_status = {"status": "error", "error": str(e)}
        
        # Check training status
        training_status = await trainer.get_training_status(db)
        
        # Get active tests count
        active_tests = await ab_test_manager.get_active_tests(db)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_status,
            "database": db_status,
            "training": {
                "sufficient_data": training_status.get('data_status', {}).get('sufficient_data', False),
                "total_feedback": training_status.get('data_status', {}).get('total_feedback', 0)
            },
            "ab_tests": {
                "active_count": len(active_tests),
                "tests": [test['test_name'] for test in active_tests]
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }