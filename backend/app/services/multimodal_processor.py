"""
Multi-modal processing service for handling text, images, and voice.
"""

import base64
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.models.leads import Lead
from app.core.config import settings

logger = logging.getLogger(__name__)


class MultiModalProcessor:
    """Service for processing multi-modal content."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the multi-modal processor."""
        self.db = db
        self.supported_formats = {
            'text': ['txt', 'html', 'markdown', 'json'],
            'image': ['png', 'jpg', 'jpeg', 'gif', 'webp'],
            'audio': ['mp3', 'wav', 'ogg', 'webm']
        }
        self.loaded_models = []
        self.cache = {}
        
    async def initialize(self):
        """Initialize processing models and resources."""
        # In production, load actual ML models here
        self.loaded_models = ['text_analyzer', 'image_processor', 'voice_transcriber']
        logger.info("Multi-modal processor initialized")
        
    async def analyze_text(self, text: str) -> Dict:
        """
        Analyze text content for entities, sentiment, and key information.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Extract keywords
        words = re.findall(r'\b[a-z]+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [k for k, _ in keywords[:10]]
        
        # Extract entities (simplified)
        entities = {}
        
        # Extract salary
        salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', text)
        if salary_match:
            entities['salary'] = salary_match.group()
            
        # Extract experience
        exp_match = re.search(r'(\d+)\+?\s*years?', text, re.I)
        if exp_match:
            entities['experience'] = exp_match.group()
            
        # Detect technologies
        tech_keywords = ['react', 'python', 'javascript', 'java', 'sql', 'aws', 'docker']
        found_tech = [tech for tech in tech_keywords if tech in text.lower()]
        if found_tech:
            entities['technologies'] = found_tech
            
        # Simple sentiment analysis (positive words vs negative)
        positive_words = ['excellent', 'great', 'amazing', 'opportunity', 'growth', 'competitive']
        negative_words = ['difficult', 'challenging', 'strict', 'demanding', 'stress']
        
        pos_count = sum(1 for word in positive_words if word in text.lower())
        neg_count = sum(1 for word in negative_words if word in text.lower())
        
        sentiment = 0.5
        if pos_count + neg_count > 0:
            sentiment = pos_count / (pos_count + neg_count)
            
        # Categorize
        category = 'general'
        if 'developer' in text.lower() or 'engineer' in text.lower():
            category = 'technology'
        elif 'sales' in text.lower() or 'marketing' in text.lower():
            category = 'business'
        elif 'design' in text.lower() or 'creative' in text.lower():
            category = 'creative'
            
        return {
            'keywords': keywords,
            'entities': entities,
            'sentiment': sentiment,
            'category': category,
            'word_count': len(words),
            'readability_score': min(100, len(words) * 0.5)
        }
        
    async def analyze_image(self, image_data: bytes) -> Dict:
        """
        Analyze image content for text, objects, and quality.
        
        Args:
            image_data: Binary image data
            
        Returns:
            Dictionary with image analysis results
        """
        try:
            from PIL import Image
            
            # Open image
            img = Image.open(BytesIO(image_data))
            
            # Get basic metadata
            analysis = {
                'format': img.format,
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'size_bytes': len(image_data)
            }
            
            # In production, perform OCR here
            # For now, simulate OCR results
            if img.width > 100 and img.height > 50:
                analysis['text'] = "Sample extracted text from image"
                analysis['has_text'] = True
            else:
                analysis['has_text'] = False
                
            # In production, perform object detection
            # For now, simulate object detection
            analysis['objects'] = []
            if img.width > 200:
                analysis['objects'] = ['logo', 'text_block']
                
            # Calculate quality score
            pixel_count = img.width * img.height
            analysis['quality_score'] = min(100, pixel_count / 10000)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {
                'error': str(e),
                'format': 'unknown',
                'width': 0,
                'height': 0
            }
            
    async def transcribe_audio(self, audio_data: bytes) -> Dict:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Binary audio data
            
        Returns:
            Dictionary with transcription results
        """
        # In production, use speech-to-text service
        # For now, simulate transcription
        
        # Generate mock transcription based on audio size
        audio_hash = hashlib.md5(audio_data).hexdigest()
        
        return {
            'text': f"This is a mock transcription for audio {audio_hash[:8]}",
            'language': 'en',
            'confidence': 0.95,
            'duration_seconds': len(audio_data) / 16000,  # Rough estimate
            'words': []
        }
        
    async def enrich_lead(
        self,
        lead_id: int,
        text_content: Optional[str] = None,
        images: Optional[List[bytes]] = None,
        audio: Optional[bytes] = None,
        extract_features: bool = True
    ) -> Dict:
        """
        Enrich a lead with multi-modal analysis.
        
        Args:
            lead_id: ID of the lead to enrich
            text_content: Optional text content
            images: Optional list of images
            audio: Optional audio content
            extract_features: Whether to extract detailed features
            
        Returns:
            Dictionary with enrichment results
        """
        enrichment = {
            'lead_id': lead_id,
            'text_features': {},
            'image_features': [],
            'audio_features': {},
            'quality_score': 0,
            'completeness': 0,
            'recommendation': 'review'
        }
        
        scores = []
        
        # Process text
        if text_content:
            text_analysis = await self.analyze_text(text_content)
            enrichment['text_features'] = text_analysis
            scores.append(text_analysis.get('readability_score', 50))
            enrichment['completeness'] += 33
            
        # Process images
        if images:
            for img_data in images:
                img_analysis = await self.analyze_image(img_data)
                enrichment['image_features'].append(img_analysis)
                scores.append(img_analysis.get('quality_score', 50))
            enrichment['completeness'] += 33
            
        # Process audio
        if audio:
            audio_analysis = await self.transcribe_audio(audio)
            enrichment['audio_features'] = audio_analysis
            scores.append(audio_analysis.get('confidence', 0.5) * 100)
            enrichment['completeness'] += 34
            
        # Calculate overall quality score
        if scores:
            enrichment['quality_score'] = sum(scores) / len(scores)
            
        # Determine recommendation
        if enrichment['quality_score'] > 80:
            enrichment['recommendation'] = 'auto_approve'
        elif enrichment['quality_score'] > 60:
            enrichment['recommendation'] = 'review'
        else:
            enrichment['recommendation'] = 'needs_improvement'
            
        # Store enrichment in database (in production)
        logger.info(f"Enriched lead {lead_id} with {enrichment['completeness']}% completeness")
        
        return enrichment
        
    async def generate_multimodal_response(
        self,
        lead: Lead,
        include_images: bool = False,
        include_voice: bool = False,
        personalization_level: str = "medium"
    ) -> Dict:
        """
        Generate a multi-modal response for a lead.
        
        Args:
            lead: Lead to respond to
            include_images: Whether to include images
            include_voice: Whether to generate voice
            personalization_level: Level of personalization
            
        Returns:
            Dictionary with response components
        """
        response = {
            'lead_id': lead.id,
            'text': '',
            'images': [],
            'voice_url': None,
            'has_images': False,
            'has_voice': False,
            'personalization_score': 0
        }
        
        # Generate text response
        base_text = f"Thank you for your interest in the {lead.title} position."
        
        if personalization_level == "high":
            response['text'] = f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {lead.title} position.
With my extensive background and proven track record, I am confident I would be
a valuable addition to your team.

I look forward to discussing how my skills align with your needs.

Best regards
            """.strip()
            response['personalization_score'] = 0.9
        elif personalization_level == "medium":
            response['text'] = f"""
Hello,

I'm very interested in the {lead.title} role.
My experience aligns well with your requirements.

Looking forward to hearing from you.

Thanks
            """.strip()
            response['personalization_score'] = 0.6
        else:
            response['text'] = base_text
            response['personalization_score'] = 0.3
            
        # Generate images if requested
        if include_images:
            # In production, generate or select relevant images
            response['images'] = ['base64_encoded_image_data']
            response['has_images'] = True
            
        # Generate voice if requested
        if include_voice:
            # In production, use text-to-speech
            response['voice_url'] = f"/audio/response_{lead.id}.mp3"
            response['has_voice'] = True
            
        return response
        
    async def cross_modal_search(
        self,
        query: str,
        search_text: bool = True,
        search_images: bool = False,
        search_audio: bool = False,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search across multiple modalities.
        
        Args:
            query: Search query
            search_text: Search in text content
            search_images: Search in image content
            search_audio: Search in audio transcriptions
            limit: Maximum results
            
        Returns:
            List of matching results
        """
        results = []
        
        # Parse query
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Search text content
        if search_text:
            # Search in leads
            stmt = select(Lead).limit(limit)
            result = await self.db.execute(stmt)
            leads = result.scalars().all()
            
            for lead in leads:
                # Calculate match score
                if lead.title and lead.description:
                    content = f"{lead.title} {lead.description}".lower()
                    matches = sum(1 for word in query_words if word in content)
                    if matches > 0:
                        score = matches / len(query_words)
                        results.append({
                            'type': 'lead',
                            'id': lead.id,
                            'title': lead.title,
                            'match_type': 'text',
                            'score': score,
                            'snippet': lead.description[:100] if lead.description else ''
                        })
                        
        # Search images (simulated)
        if search_images:
            # In production, search through indexed image content
            if 'visual' in query_lower or 'image' in query_lower:
                results.append({
                    'type': 'image',
                    'id': 'img_001',
                    'title': 'Sample Image Result',
                    'match_type': 'image',
                    'score': 0.7,
                    'snippet': 'Image containing relevant visual content'
                })
                
        # Search audio (simulated)
        if search_audio:
            # In production, search through transcribed audio
            if 'voice' in query_lower or 'audio' in query_lower:
                results.append({
                    'type': 'audio',
                    'id': 'audio_001',
                    'title': 'Sample Audio Result',
                    'match_type': 'audio',
                    'score': 0.6,
                    'snippet': 'Audio transcript matching query'
                })
                
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:limit]
        
    async def generate_insights(
        self,
        time_range: str = "last_7_days",
        modalities: List[str] = None
    ) -> Dict:
        """
        Generate insights from multi-modal data.
        
        Args:
            time_range: Time range for analysis
            modalities: List of modalities to analyze
            
        Returns:
            Dictionary with insights
        """
        if modalities is None:
            modalities = ['text', 'image', 'voice']
            
        # Calculate date range
        if time_range == "last_7_days":
            start_date = datetime.now() - timedelta(days=7)
        elif time_range == "last_30_days":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=1)
            
        # Get leads in time range
        stmt = select(func.count(Lead.id)).where(
            Lead.created_at >= start_date
        )
        result = await self.db.execute(stmt)
        total_leads = result.scalar() or 0
        
        # Generate insights
        insights = {
            'time_range': time_range,
            'total_leads': total_leads,
            'text_only': int(total_leads * 0.7),  # Simulated
            'with_images': int(total_leads * 0.2),  # Simulated
            'voice_interactions': int(total_leads * 0.1),  # Simulated
            'avg_quality_score': 0.75,
            'top_keywords': ['remote', 'developer', 'senior'],
            'engagement_rate': 0.65,
            'modality_distribution': {}
        }
        
        # Calculate modality distribution
        for modality in modalities:
            if modality == 'text':
                insights['modality_distribution'][modality] = 0.7
            elif modality == 'image':
                insights['modality_distribution'][modality] = 0.2
            elif modality == 'voice':
                insights['modality_distribution'][modality] = 0.1
                
        # Add recommendations
        insights['recommendations'] = []
        if insights['with_images'] < insights['text_only'] * 0.3:
            insights['recommendations'].append("Consider adding more visual content")
        if insights['voice_interactions'] < insights['total_leads'] * 0.2:
            insights['recommendations'].append("Voice interactions could improve engagement")
            
        return insights