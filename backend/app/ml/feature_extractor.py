"""
Feature extraction service for lead scoring ML pipeline.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder
import structlog

logger = structlog.get_logger(__name__)


class FeatureExtractor:
    """Extract features from lead data for ML model training and prediction."""
    
    def __init__(self):
        self.tfidf_title = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self.tfidf_description = TfidfVectorizer(
            max_features=200,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self.location_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # High-value keywords for different categories
        self.high_value_keywords = {
            'salary': [
                'salary', 'annual', 'yearly', 'k/year', 'per year', 'benefits',
                'health insurance', 'dental', 'vision', '401k', 'retirement',
                'vacation', 'pto', 'paid time off'
            ],
            'experience': [
                'experienced', 'senior', 'lead', 'manager', 'director',
                'expert', 'specialist', 'professional', 'certified'
            ],
            'technology': [
                'python', 'javascript', 'react', 'node', 'aws', 'docker',
                'kubernetes', 'sql', 'mongodb', 'postgresql', 'redis',
                'machine learning', 'ai', 'data science'
            ],
            'urgency': [
                'immediate', 'asap', 'urgent', 'start now', 'begin immediately',
                'right away', 'quickly', 'fast track'
            ],
            'company_size': [
                'startup', 'fortune 500', 'enterprise', 'established',
                'growing company', 'team of', 'employees'
            ]
        }
        
        # Location popularity scores (can be updated based on historical data)
        self.location_scores = {
            'san francisco': 0.9,
            'new york': 0.85,
            'seattle': 0.8,
            'austin': 0.75,
            'denver': 0.7,
            'remote': 0.95
        }
    
    def extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract features from text content."""
        if not text:
            return {}
            
        text = text.lower()
        features = {}
        
        # Basic text statistics
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['sentence_count'] = len([s for s in text.split('.') if s.strip()])
        features['avg_word_length'] = np.mean([len(word) for word in text.split()])
        
        # Keyword matching scores
        for category, keywords in self.high_value_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            features[f'{category}_keyword_count'] = matches
            features[f'{category}_keyword_density'] = matches / max(len(text.split()), 1)
        
        # Email and phone patterns
        features['has_email'] = 1 if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text) else 0
        features['has_phone'] = 1 if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text) else 0
        
        # Salary information
        salary_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if salary_match:
            features['salary_mentioned'] = 1
            features['salary_amount'] = float(salary_match.group(1).replace(',', ''))
        else:
            features['salary_mentioned'] = 0
            features['salary_amount'] = 0
        
        # Experience level indicators
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*experience',
            r'(\d+)\+?\s*yrs?\s*exp',
            r'minimum\s*(\d+)\s*years?'
        ]
        
        max_experience = 0
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                max_experience = max(max_experience, max(int(match) for match in matches))
        
        features['experience_years'] = max_experience
        features['has_experience_req'] = 1 if max_experience > 0 else 0
        
        return features
    
    def extract_temporal_features(self, posted_at: Optional[datetime], scraped_at: datetime) -> Dict[str, float]:
        """Extract temporal features from posting dates."""
        features = {}
        
        if posted_at:
            # Time since posting
            time_diff = scraped_at - posted_at
            features['hours_since_posted'] = time_diff.total_seconds() / 3600
            features['days_since_posted'] = time_diff.days
            
            # Day of week (0=Monday, 6=Sunday)
            features['posted_day_of_week'] = posted_at.weekday()
            features['posted_is_weekend'] = 1 if posted_at.weekday() >= 5 else 0
            
            # Hour of day
            features['posted_hour'] = posted_at.hour
            features['posted_is_business_hours'] = 1 if 9 <= posted_at.hour <= 17 else 0
            
            # Freshness score (higher for recent posts)
            features['freshness_score'] = max(0, 1 - (time_diff.total_seconds() / (7 * 24 * 3600)))
        else:
            # Default values when posted_at is not available
            features['hours_since_posted'] = 0
            features['days_since_posted'] = 0
            features['posted_day_of_week'] = 0
            features['posted_is_weekend'] = 0
            features['posted_hour'] = 12
            features['posted_is_business_hours'] = 1
            features['freshness_score'] = 0.5
        
        # Current time features
        features['scraped_day_of_week'] = scraped_at.weekday()
        features['scraped_hour'] = scraped_at.hour
        features['scraped_is_business_hours'] = 1 if 9 <= scraped_at.hour <= 17 else 0
        
        return features
    
    def extract_location_features(self, location_name: Optional[str]) -> Dict[str, float]:
        """Extract location-based features."""
        features = {}
        
        if not location_name:
            features['location_popularity'] = 0.5
            features['is_remote'] = 0
            features['is_major_city'] = 0
            return features
        
        location_lower = location_name.lower()
        
        # Location popularity score
        features['location_popularity'] = self.location_scores.get(location_lower, 0.5)
        
        # Remote work indicator
        features['is_remote'] = 1 if 'remote' in location_lower else 0
        
        # Major city indicator
        major_cities = ['san francisco', 'new york', 'los angeles', 'chicago', 'seattle', 'austin', 'denver', 'boston']
        features['is_major_city'] = 1 if any(city in location_lower for city in major_cities) else 0
        
        return features
    
    def extract_category_features(self, category: Optional[str], subcategory: Optional[str]) -> Dict[str, float]:
        """Extract category-based features."""
        features = {}
        
        if category:
            category_lower = category.lower()
            # High-value categories
            high_value_categories = ['software/qa/dba', 'engineering', 'marketing/pr/ad', 'finance', 'legal/paralegal']
            features['is_high_value_category'] = 1 if category_lower in high_value_categories else 0
            
            # Tech-related categories
            tech_categories = ['software/qa/dba', 'engineering', 'systems/network']
            features['is_tech_category'] = 1 if category_lower in tech_categories else 0
        else:
            features['is_high_value_category'] = 0
            features['is_tech_category'] = 0
        
        return features
    
    def extract_historical_features(self, lead_data: Dict[str, Any], historical_stats: Optional[Dict] = None) -> Dict[str, float]:
        """Extract features based on historical performance data."""
        features = {}
        
        if not historical_stats:
            # Default values when no historical data is available
            features['avg_success_rate'] = 0.5
            features['similar_leads_count'] = 0
            features['location_success_rate'] = 0.5
            features['category_success_rate'] = 0.5
            return features
        
        # Success rates based on similar leads
        features['avg_success_rate'] = historical_stats.get('avg_success_rate', 0.5)
        features['similar_leads_count'] = historical_stats.get('similar_leads_count', 0)
        features['location_success_rate'] = historical_stats.get('location_success_rate', 0.5)
        features['category_success_rate'] = historical_stats.get('category_success_rate', 0.5)
        
        return features
    
    def extract_features(self, lead_data: Dict[str, Any], historical_stats: Optional[Dict] = None) -> Dict[str, float]:
        """Extract all features for a single lead."""
        try:
            features = {}
            
            # Text features from title and description
            title_features = self.extract_text_features(lead_data.get('title', ''))
            desc_features = self.extract_text_features(lead_data.get('description', ''))
            
            # Combine text features with prefixes
            for key, value in title_features.items():
                features[f'title_{key}'] = value
            for key, value in desc_features.items():
                features[f'desc_{key}'] = value
            
            # Temporal features
            posted_at = lead_data.get('posted_at')
            scraped_at = lead_data.get('scraped_at', datetime.utcnow())
            temporal_features = self.extract_temporal_features(posted_at, scraped_at)
            features.update(temporal_features)
            
            # Location features
            location_name = lead_data.get('location_name') or lead_data.get('location', {}).get('name')
            location_features = self.extract_location_features(location_name)
            features.update(location_features)
            
            # Category features
            category_features = self.extract_category_features(
                lead_data.get('category'),
                lead_data.get('subcategory')
            )
            features.update(category_features)
            
            # Historical features
            historical_features = self.extract_historical_features(lead_data, historical_stats)
            features.update(historical_features)
            
            # Basic metadata features
            features['has_email'] = 1 if lead_data.get('email') else 0
            features['has_phone'] = 1 if lead_data.get('phone') else 0
            features['has_contact_name'] = 1 if lead_data.get('contact_name') else 0
            features['price'] = float(lead_data.get('price', 0))
            
            return features
            
        except Exception as e:
            logger.error("Error extracting features", error=str(e), lead_id=lead_data.get('id'))
            # Return default features to avoid pipeline failure
            return self._get_default_features()
    
    def extract_batch_features(self, leads_data: List[Dict[str, Any]], 
                             historical_stats: Optional[List[Dict]] = None) -> pd.DataFrame:
        """Extract features for multiple leads."""
        try:
            feature_dicts = []
            
            for i, lead_data in enumerate(leads_data):
                hist_stats = historical_stats[i] if historical_stats else None
                features = self.extract_features(lead_data, hist_stats)
                features['lead_id'] = lead_data.get('id')
                feature_dicts.append(features)
            
            df = pd.DataFrame(feature_dicts)
            
            # Handle missing values
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            logger.error("Error extracting batch features", error=str(e))
            raise
    
    def fit_transform(self, leads_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Fit feature extractors and transform data (used during training)."""
        try:
            logger.info("Fitting feature extractors", num_leads=len(leads_data))
            
            # Extract basic features
            features_df = self.extract_batch_features(leads_data)
            
            # Prepare text data for TF-IDF
            titles = [lead.get('title', '') for lead in leads_data]
            descriptions = [lead.get('description', '') for lead in leads_data]
            
            # Fit and transform TF-IDF
            title_tfidf = self.tfidf_title.fit_transform(titles).toarray()
            desc_tfidf = self.tfidf_description.fit_transform(descriptions).toarray()
            
            # Add TF-IDF features to dataframe
            title_cols = [f'title_tfidf_{i}' for i in range(title_tfidf.shape[1])]
            desc_cols = [f'desc_tfidf_{i}' for i in range(desc_tfidf.shape[1])]
            
            tfidf_df = pd.DataFrame(
                np.hstack([title_tfidf, desc_tfidf]),
                columns=title_cols + desc_cols
            )
            
            # Combine features
            features_df = pd.concat([features_df.reset_index(drop=True), tfidf_df], axis=1)
            
            # Fit encoders for categorical features
            locations = [lead.get('location', {}).get('name', 'unknown') for lead in leads_data]
            categories = [lead.get('category', 'unknown') for lead in leads_data]
            
            # Fit label encoders
            self.location_encoder.fit(locations)
            self.category_encoder.fit(categories)
            
            # Apply encoders
            features_df['location_encoded'] = self.location_encoder.transform(
                [lead.get('location', {}).get('name', 'unknown') for lead in leads_data]
            )
            features_df['category_encoded'] = self.category_encoder.transform(
                [lead.get('category', 'unknown') for lead in leads_data]
            )
            
            # Fit scaler on numerical features
            numerical_cols = features_df.select_dtypes(include=[np.number]).columns
            numerical_cols = [col for col in numerical_cols if col not in ['lead_id']]
            
            features_df[numerical_cols] = self.scaler.fit_transform(features_df[numerical_cols])
            
            self.is_fitted = True
            
            logger.info("Feature extraction completed", 
                       num_features=len(features_df.columns), 
                       num_samples=len(features_df))
            
            return features_df
            
        except Exception as e:
            logger.error("Error in fit_transform", error=str(e))
            raise
    
    def transform(self, leads_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Transform data using fitted extractors (used during prediction)."""
        if not self.is_fitted:
            raise ValueError("Feature extractor must be fitted before transform")
        
        try:
            # Extract basic features
            features_df = self.extract_batch_features(leads_data)
            
            # Prepare text data for TF-IDF
            titles = [lead.get('title', '') for lead in leads_data]
            descriptions = [lead.get('description', '') for lead in leads_data]
            
            # Transform using fitted TF-IDF
            title_tfidf = self.tfidf_title.transform(titles).toarray()
            desc_tfidf = self.tfidf_description.transform(descriptions).toarray()
            
            # Add TF-IDF features
            title_cols = [f'title_tfidf_{i}' for i in range(title_tfidf.shape[1])]
            desc_cols = [f'desc_tfidf_{i}' for i in range(desc_tfidf.shape[1])]
            
            tfidf_df = pd.DataFrame(
                np.hstack([title_tfidf, desc_tfidf]),
                columns=title_cols + desc_cols
            )
            
            # Combine features
            features_df = pd.concat([features_df.reset_index(drop=True), tfidf_df], axis=1)
            
            # Apply encoders
            locations = [lead.get('location', {}).get('name', 'unknown') for lead in leads_data]
            categories = [lead.get('category', 'unknown') for lead in leads_data]
            
            # Handle unknown categories gracefully
            encoded_locations = []
            for loc in locations:
                try:
                    encoded_locations.append(self.location_encoder.transform([loc])[0])
                except ValueError:
                    # Unknown location, use a default encoding
                    encoded_locations.append(-1)
            
            encoded_categories = []
            for cat in categories:
                try:
                    encoded_categories.append(self.category_encoder.transform([cat])[0])
                except ValueError:
                    # Unknown category, use a default encoding
                    encoded_categories.append(-1)
            
            features_df['location_encoded'] = encoded_locations
            features_df['category_encoded'] = encoded_categories
            
            # Apply scaler
            numerical_cols = features_df.select_dtypes(include=[np.number]).columns
            numerical_cols = [col for col in numerical_cols if col not in ['lead_id']]
            
            features_df[numerical_cols] = self.scaler.transform(features_df[numerical_cols])
            
            return features_df
            
        except Exception as e:
            logger.error("Error in transform", error=str(e))
            raise
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default feature values for error cases."""
        return {
            'title_text_length': 0, 'title_word_count': 0, 'title_salary_keyword_count': 0,
            'desc_text_length': 0, 'desc_word_count': 0, 'desc_salary_keyword_count': 0,
            'hours_since_posted': 0, 'days_since_posted': 0, 'freshness_score': 0.5,
            'location_popularity': 0.5, 'is_remote': 0, 'is_major_city': 0,
            'is_high_value_category': 0, 'is_tech_category': 0,
            'has_email': 0, 'has_phone': 0, 'has_contact_name': 0, 'price': 0,
            'avg_success_rate': 0.5, 'similar_leads_count': 0
        }
    
    def get_feature_importance_names(self) -> List[str]:
        """Get human-readable feature names for model interpretation."""
        base_features = [
            'Title Length', 'Title Word Count', 'Title Salary Keywords',
            'Description Length', 'Description Word Count', 'Description Salary Keywords',
            'Hours Since Posted', 'Days Since Posted', 'Freshness Score',
            'Location Popularity', 'Is Remote', 'Is Major City',
            'High Value Category', 'Tech Category',
            'Has Email', 'Has Phone', 'Has Contact Name', 'Price Listed',
            'Historical Success Rate', 'Similar Leads Count'
        ]
        
        # Add TF-IDF feature names
        if self.is_fitted:
            tfidf_features = [f'Title TF-IDF {i}' for i in range(len(self.tfidf_title.vocabulary_))]
            tfidf_features += [f'Desc TF-IDF {i}' for i in range(len(self.tfidf_description.vocabulary_))]
            base_features.extend(tfidf_features)
        
        return base_features