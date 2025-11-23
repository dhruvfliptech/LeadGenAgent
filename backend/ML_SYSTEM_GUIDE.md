# Machine Learning Lead Scoring System

A comprehensive machine learning system for scoring and ranking leads based on user interactions and feedback.

## Architecture Overview

The ML system consists of several interconnected components:

1. **Feature Extraction** (`app/ml/feature_extractor.py`)
   - Text processing (TF-IDF, keyword matching)
   - Temporal features (time-based patterns)
   - Location and category analysis
   - Historical performance metrics

2. **Lead Scoring** (`app/ml/lead_scorer.py`)
   - XGBoost-based scoring model
   - Model versioning and management
   - Real-time and batch prediction
   - Feature importance analysis

3. **Model Training** (`app/ml/model_trainer.py`)
   - Automated retraining pipeline
   - Performance monitoring
   - Training data management
   - Model lifecycle management

4. **Feedback Processing** (`app/ml/feedback_processor.py`)
   - User interaction tracking
   - Implicit feedback generation
   - Feedback confidence scoring
   - Analytics and reporting

5. **A/B Testing** (`app/ml/ab_testing.py`)
   - Model comparison framework
   - Statistical significance testing
   - Traffic allocation management
   - Performance analysis

## API Endpoints

### Core Scoring Endpoints

#### Score Single Lead
```http
POST /api/v1/ml/score
Content-Type: application/json

{
  "lead_id": 123,
  "title": "Software Engineer Position",
  "description": "Looking for Python developer...",
  "category": "software/qa/dba",
  "location_name": "San Francisco",
  "price": 120000,
  "email": "recruiter@company.com",
  "posted_at": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "lead_id": 123,
  "score": 85,
  "confidence": 0.85,
  "model_version": "v20240101_120000_abc12345",
  "feature_importance": {
    "Title Salary Keywords": 0.25,
    "Location Popularity": 0.20,
    "Tech Category": 0.15
  },
  "prediction_time": "2024-01-01T12:00:00Z"
}
```

#### Batch Score Leads
```http
POST /api/v1/ml/batch-score
Content-Type: application/json

{
  "leads": [
    {
      "lead_id": 123,
      "title": "Software Engineer",
      // ... other fields
    },
    // ... more leads
  ]
}
```

### Feedback Endpoints

#### Record User Feedback
```http
POST /api/v1/ml/feedback
Content-Type: application/json

{
  "lead_id": 123,
  "action_type": "contact",
  "user_rating": 90,
  "interaction_duration": 180,
  "contact_successful": true,
  "conversion_value": 5000,
  "session_id": "session_abc123"
}
```

#### Record Implicit Feedback
```http
POST /api/v1/ml/feedback/implicit
Content-Type: application/json

{
  "session_id": "session_abc123",
  "interactions": [
    {
      "lead_id": 123,
      "type": "view",
      "duration": 300
    },
    {
      "lead_id": 124,
      "type": "archive",
      "duration": 5
    }
  ]
}
```

### Model Management Endpoints

#### Get Model Metrics
```http
GET /api/v1/ml/metrics
```

#### Trigger Model Retraining
```http
POST /api/v1/ml/retrain
Content-Type: application/json

{
  "force_retrain": false,
  "validation_split": 0.2,
  "params": {
    "max_depth": 8,
    "learning_rate": 0.05
  }
}
```

#### List Available Models
```http
GET /api/v1/ml/models
```

#### Activate Specific Model
```http
POST /api/v1/ml/models/v20240101_120000_abc12345/activate
```

### A/B Testing Endpoints

#### Create A/B Test
```http
POST /api/v1/ml/ab-tests
Content-Type: application/json

{
  "test_name": "model_comparison_v1",
  "variants": [
    {
      "variant_name": "control",
      "model_version": "v20240101_120000_abc12345",
      "traffic_percentage": 50,
      "is_control": true
    },
    {
      "variant_name": "experimental",
      "model_version": "v20240102_120000_def67890",
      "traffic_percentage": 50,
      "is_control": false
    }
  ]
}
```

#### Score with A/B Test
```http
POST /api/v1/ml/ab-tests/model_comparison_v1/score
Content-Type: application/json

{
  "test_name": "model_comparison_v1",
  "lead_data": {
    "lead_id": 123,
    "title": "Software Engineer",
    // ... other fields
  },
  "user_id": "user_123"
}
```

#### Get A/B Test Results
```http
GET /api/v1/ml/ab-tests/model_comparison_v1/results
```

#### Stop A/B Test
```http
POST /api/v1/ml/ab-tests/model_comparison_v1/stop?winner_variant=experimental
```

### Analytics Endpoints

#### Get Feedback Analytics
```http
GET /api/v1/ml/analytics/feedback?days=30
```

#### Get Lead Feedback History
```http
GET /api/v1/ml/feedback/123
```

#### Health Check
```http
GET /api/v1/ml/health
```

## Features

### Text Feature Extraction

The system extracts comprehensive features from lead text:

- **Basic Statistics**: Length, word count, sentence count
- **Keyword Matching**: High-value terms by category (salary, experience, technology)
- **Contact Information**: Email and phone pattern detection
- **Salary Analysis**: Salary amount extraction and normalization
- **Experience Requirements**: Years of experience extraction

### Temporal Features

Time-based features that capture posting patterns:

- **Freshness**: Time since posting (higher scores for recent posts)
- **Business Hours**: Posted during business hours indicator
- **Day of Week**: Weekend vs weekday posting patterns
- **Posting Behavior**: Time patterns that correlate with lead quality

### Location Features

Geographic and location-based scoring:

- **Market Popularity**: Major city and market desirability scores
- **Remote Work**: Remote position indicators
- **Location Success Rates**: Historical performance by location

### Category Features

Industry and job category analysis:

- **High-Value Categories**: Technology, finance, engineering focus
- **Category Success Rates**: Historical performance by category
- **Subcategory Analysis**: Detailed job type classification

### Historical Features

Past performance integration:

- **Similar Lead Performance**: Success rates for similar leads
- **Location Track Record**: Area-specific success patterns
- **Category Performance**: Industry-specific success rates

## Model Training Pipeline

### Automatic Retraining

The system automatically checks for retraining needs based on:

- **Model Age**: Models older than 7 days (configurable)
- **New Data**: Sufficient new feedback samples (50+ samples)
- **Performance Degradation**: F1 score drop >5% (configurable)
- **Data Availability**: Minimum 100 training samples required

### Training Process

1. **Data Collection**: Gather leads with feedback
2. **Feature Extraction**: Process all features
3. **Target Calculation**: Convert feedback to scores (0-1)
4. **Model Training**: XGBoost with cross-validation
5. **Evaluation**: Calculate performance metrics
6. **Deployment**: Activate new model if performance improves

### Target Score Calculation

User feedback is converted to target scores:

- **Direct Rating** (0-100): Use as-is → 0-1 scale
- **Conversion**: 1.0 (perfect score)
- **Successful Contact**: 0.9
- **Contact Attempt**: 0.6-0.8 (based on outcome)
- **Extended View** (>5min): 0.7
- **Normal View** (>2min): 0.5
- **Quick Archive** (<30sec): 0.1-0.3

## A/B Testing Framework

### Statistical Analysis

The system performs rigorous statistical testing:

- **Two-Proportion Z-Test**: Compare conversion rates
- **Confidence Intervals**: 95% CI for effect size
- **Minimum Sample Size**: 100 samples per variant
- **Significance Level**: p < 0.05
- **Minimum Effect Size**: 2% improvement required

### Traffic Allocation

- **Consistent Assignment**: Hash-based user assignment
- **Flexible Distribution**: Any percentage split
- **Control Groups**: Automatic baseline comparison

### Recommendations

The system provides actionable recommendations:
- Statistical significance assessment
- Sample size adequacy warnings
- Effect size interpretation
- Runtime optimization suggestions

## Performance Monitoring

### Model Metrics

Tracked performance indicators:

- **Classification Metrics**: Precision, recall, F1-score, AUC-ROC
- **Business Metrics**: Conversion rate, contact success rate
- **Efficiency Metrics**: Prediction latency, throughput

### Feedback Analytics

- **Action Distribution**: View, contact, convert, archive patterns
- **Confidence Tracking**: Feedback reliability scores
- **Temporal Patterns**: Usage and success trends
- **Source Analysis**: Manual vs. implicit feedback performance

### Alerts and Monitoring

- **Performance Degradation**: Automatic detection
- **Data Quality Issues**: Missing or inconsistent data
- **Model Availability**: Service health monitoring
- **Training Pipeline**: Automated retraining status

## Configuration

### Environment Variables

```bash
# ML Model Settings
MODEL_DIR="/app/models"
MIN_TRAINING_SAMPLES=100
RETRAIN_INTERVAL_DAYS=7
RETRAIN_THRESHOLD_F1=0.05

# A/B Testing
AB_TEST_MIN_SAMPLE_SIZE=100
AB_TEST_SIGNIFICANCE_LEVEL=0.05
AB_TEST_MIN_EFFECT_SIZE=0.02

# Feature Extraction
TFIDF_MAX_FEATURES_TITLE=100
TFIDF_MAX_FEATURES_DESC=200
```

### Model Hyperparameters

Default XGBoost parameters (configurable):

```python
{
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42
}
```

## Database Schema

### Lead Feedback Table

```sql
CREATE TABLE lead_feedback (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    user_rating FLOAT,
    action_type VARCHAR(50) NOT NULL,
    interaction_duration FLOAT,
    feedback_source VARCHAR(50) NOT NULL DEFAULT 'manual',
    feedback_confidence FLOAT NOT NULL DEFAULT 1.0,
    contact_successful BOOLEAN,
    contact_response_time FLOAT,
    conversion_value FLOAT,
    session_id VARCHAR(255),
    user_agent TEXT,
    ip_address VARCHAR(45),
    model_version VARCHAR(50),
    prediction_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Model Metrics Table

```sql
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL DEFAULT 'xgboost',
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    auc_roc FLOAT,
    accuracy FLOAT,
    conversion_rate FLOAT,
    contact_success_rate FLOAT,
    avg_prediction_score FLOAT,
    training_samples INTEGER,
    validation_samples INTEGER,
    feature_count INTEGER,
    training_duration FLOAT,
    is_active BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### A/B Test Variants Table

```sql
CREATE TABLE ab_test_variants (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    variant_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    traffic_percentage FLOAT NOT NULL,
    is_control BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sample_size INTEGER DEFAULT 0,
    conversion_rate FLOAT,
    avg_score FLOAT,
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,
    statistical_significance FLOAT,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Usage Examples

### Basic Lead Scoring

```python
from app.ml.lead_scorer import LeadScorer

# Initialize scorer
scorer = LeadScorer()
scorer.load_model()  # Load latest model

# Score a lead
lead_data = {
    'id': 123,
    'title': 'Senior Python Developer',
    'description': 'Looking for experienced Python developer...',
    'category': 'software/qa/dba',
    'location_name': 'San Francisco',
    'price': 150000
}

prediction = scorer.predict_single(lead_data)
print(f"Lead score: {prediction['score']}/100")
print(f"Confidence: {prediction['confidence']:.2%}")
```

### Training a New Model

```python
from app.ml.model_trainer import ModelTrainer

# Initialize trainer
trainer = ModelTrainer()

# Check if retraining is needed
check_result = await trainer.check_retraining_needed(db)
print(f"Should retrain: {check_result['should_retrain']}")
print(f"Reasons: {check_result['reasons']}")

# Train new model
training_result = await trainer.train_new_model(db)
print(f"New model version: {training_result['model_version']}")
print(f"F1 Score: {training_result['metrics']['f1_score']:.3f}")
```

### Recording Feedback

```python
from app.ml.feedback_processor import FeedbackProcessor

processor = FeedbackProcessor()

# Record user contact action
feedback_data = {
    'lead_id': 123,
    'action_type': 'contact',
    'contact_successful': True,
    'interaction_duration': 180,  # 3 minutes
    'session_id': 'session_abc123'
}

result = await processor.process_user_feedback(db, feedback_data)
print(f"Feedback recorded with confidence: {result['confidence']:.2f}")
```

### Running A/B Tests

```python
from app.ml.ab_testing import ABTestManager

ab_manager = ABTestManager()

# Create A/B test
test_config = {
    'test_name': 'model_comparison_v1',
    'variants': [
        {
            'variant_name': 'control',
            'model_version': 'v20240101_120000_abc123',
            'traffic_percentage': 50,
            'is_control': True
        },
        {
            'variant_name': 'experimental',
            'model_version': 'v20240102_120000_def456',
            'traffic_percentage': 50,
            'is_control': False
        }
    ]
}

result = await ab_manager.create_ab_test(db, test_config)
print(f"A/B test created: {result['test_name']}")

# Score with A/B test
prediction = await ab_manager.score_with_ab_test(
    db, 'model_comparison_v1', lead_data, user_id='user123'
)
print(f"Assigned variant: {prediction['ab_test_variant']}")
print(f"Score: {prediction['score']}")
```

## Maintenance and Operations

### Model Cleanup

```bash
# Clean up old models (keep latest 5)
curl -X POST http://localhost:8000/api/v1/ml/cleanup/models?keep_count=5
```

### Feedback Cleanup

```bash
# Clean up feedback older than 1 year
curl -X POST http://localhost:8000/api/v1/ml/cleanup/feedback?retention_days=365
```

### Health Monitoring

```bash
# Check ML system health
curl http://localhost:8000/api/v1/ml/health
```

### Performance Monitoring

```bash
# Get current metrics
curl http://localhost:8000/api/v1/ml/metrics

# Get feedback analytics for last 30 days
curl http://localhost:8000/api/v1/ml/analytics/feedback?days=30
```

## Best Practices

### Data Quality

1. **Consistent Feedback**: Ensure consistent user feedback patterns
2. **Diverse Training Data**: Include various lead types and outcomes
3. **Regular Validation**: Monitor prediction accuracy over time
4. **Outlier Detection**: Identify and handle unusual leads

### Model Management

1. **Version Control**: Track all model versions and changes
2. **A/B Testing**: Always test new models before full deployment
3. **Rollback Strategy**: Keep previous models for quick rollback
4. **Performance Monitoring**: Set up alerts for performance degradation

### Scalability

1. **Batch Processing**: Use batch endpoints for bulk operations
2. **Caching**: Cache model predictions when appropriate
3. **Async Processing**: Use background tasks for training
4. **Load Balancing**: Scale horizontally for high throughput

### Security

1. **Data Privacy**: Anonymize user data when possible
2. **Access Control**: Restrict model management endpoints
3. **Audit Logging**: Track all model changes and predictions
4. **Input Validation**: Sanitize all input data

This comprehensive ML system provides a robust foundation for lead scoring with continuous learning capabilities, statistical rigor, and production-ready monitoring.