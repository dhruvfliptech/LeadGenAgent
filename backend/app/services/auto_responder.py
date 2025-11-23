"""
Auto-responder service with AI-powered personalized responses.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

try:
    import openai
except ImportError:
    openai = None
    
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from app.core.database import get_db
from app.models.leads import Lead
from app.models.response_templates import ResponseTemplate
# Note: AutoResponse and ResponseVariable don't exist yet
from app.core.config import settings


logger = logging.getLogger(__name__)


class AIProvider:
    """AI provider interface for generating responses."""
    
    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        
        if provider_type == "openai":
            if openai:
                self.client = openai.AsyncOpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
            else:
                self.client = None
        elif provider_type == "anthropic":
            if Anthropic:
                self.client = Anthropic(api_key=getattr(settings, 'ANTHROPIC_API_KEY', None))
            else:
                self.client = None
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")
    
    async def generate_response(
        self, 
        prompt: str, 
        tone: str = "professional", 
        max_length: int = 500
    ) -> str:
        """Generate AI-powered response."""
        try:
            if self.provider_type == "openai":
                return await self._generate_openai_response(prompt, tone, max_length)
            elif self.provider_type == "anthropic":
                return await self._generate_anthropic_response(prompt, tone, max_length)
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            raise
    
    async def _generate_openai_response(self, prompt: str, tone: str, max_length: int) -> str:
        """Generate response using OpenAI."""
        system_message = f"""
        You are an expert sales professional writing personalized responses to potential leads.
        Write in a {tone} tone and keep the response under {max_length} characters.
        Be specific, helpful, and focus on building rapport.
        Always include a clear call to action.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_length // 4,  # Rough approximation
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_anthropic_response(self, prompt: str, tone: str, max_length: int) -> str:
        """Generate response using Anthropic Claude."""
        system_message = f"""
        You are an expert sales professional writing personalized responses to potential leads.
        Write in a {tone} tone and keep the response under {max_length} characters.
        Be specific, helpful, and focus on building rapport.
        Always include a clear call to action.
        """
        
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_length // 4,
            system=system_message,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()


class TemplateEngine:
    """Template processing and variable substitution."""
    
    def __init__(self, db: Session):
        self.db = db
        self._load_variables()
    
    def _load_variables(self):
        """Load available template variables from database."""
        self.variables = {}
        vars_query = self.db.query(ResponseVariable).filter(ResponseVariable.is_active == True).all()
        
        for var in vars_query:
            self.variables[var.name] = {
                'display_name': var.display_name,
                'description': var.description,
                'type': var.variable_type,
                'source_field': var.source_field,
                'default_value': var.default_value
            }
    
    def extract_lead_data(self, lead: Lead) -> Dict[str, str]:
        """Extract data from lead for template variables."""
        data = {
            'lead_title': lead.title or '',
            'lead_description': lead.description or '',
            'lead_price': str(lead.price) if lead.price else '',
            'lead_category': lead.category or '',
            'lead_location': lead.location.name if lead.location else '',
            'contact_name': lead.contact_name or 'there',
            'posting_date': lead.posted_at.strftime('%Y-%m-%d') if lead.posted_at else '',
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.now().strftime('%H:%M'),
        }
        
        # Add custom fields based on variable definitions
        for var_name, var_config in self.variables.items():
            if var_config['source_field'] and hasattr(lead, var_config['source_field']):
                value = getattr(lead, var_config['source_field'])
                data[var_name] = str(value) if value is not None else var_config['default_value']
            elif var_name not in data:
                data[var_name] = var_config['default_value'] or ''
        
        return data
    
    def render_template(self, template_text: str, data: Dict[str, str]) -> str:
        """Render template with variable substitution."""
        try:
            # Simple template substitution using format strings
            rendered = template_text
            
            for var_name, value in data.items():
                placeholder = f"{{{var_name}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            # Clean up any remaining placeholders
            import re
            rendered = re.sub(r'\{[^}]+\}', '', rendered)
            
            return rendered.strip()
        
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template_text


class ABTestingManager:
    """A/B testing manager for response templates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def select_template_variant(self, base_template_id: int) -> ResponseTemplate:
        """Select template variant based on A/B testing weights."""
        base_template = self.db.query(ResponseTemplate).filter(
            ResponseTemplate.id == base_template_id
        ).first()
        
        if not base_template:
            raise ValueError(f"Template {base_template_id} not found")
        
        # Get test variants
        variants = self.db.query(ResponseTemplate).filter(
            and_(
                ResponseTemplate.control_template_id == base_template_id,
                ResponseTemplate.is_active == True,
                ResponseTemplate.is_test_variant == True
            )
        ).all()
        
        if not variants:
            return base_template
        
        # Calculate selection probability
        total_weight = base_template.test_weight
        for variant in variants:
            total_weight += variant.test_weight
        
        # Random selection based on weights
        rand_value = random.uniform(0, total_weight)
        current_weight = 0
        
        # Check base template first
        current_weight += base_template.test_weight
        if rand_value <= current_weight:
            return base_template
        
        # Check variants
        for variant in variants:
            current_weight += variant.test_weight
            if rand_value <= current_weight:
                return variant
        
        # Fallback to base template
        return base_template
    
    def record_template_usage(self, template_id: int, outcome: str):
        """Record template usage for A/B testing analytics."""
        template = self.db.query(ResponseTemplate).filter(
            ResponseTemplate.id == template_id
        ).first()
        
        if template:
            template.sent_count += 1
            
            if outcome == "response":
                template.response_count += 1
            elif outcome == "conversion":
                template.conversion_count += 1
            
            self.db.commit()


class AutoResponderService:
    """Main auto-responder service."""
    
    def __init__(self):
        self.ai_provider = AIProvider(getattr(settings, 'AI_PROVIDER', 'openai'))
        self.db = None  # Will be set per request
        self.template_engine = None  # Will be set per request
        self.ab_testing = None  # Will be set per request
    
    async def create_auto_response(
        self,
        lead_id: int,
        template_id: int,
        delay_minutes: int = 0,
        personalization_config: Optional[Dict] = None
    ) -> AutoResponse:
        """Create an auto-response for a lead."""
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Check if already responded to this lead
            existing_response = self.db.query(AutoResponse).filter(
                AutoResponse.lead_id == lead_id
            ).first()
            
            if existing_response:
                logger.warning(f"Auto-response already exists for lead {lead_id}")
                return existing_response
            
            # Select template variant for A/B testing
            template = self.ab_testing.select_template_variant(template_id)
            
            # Extract lead data for personalization
            lead_data = self.template_engine.extract_lead_data(lead)
            
            # Render base template
            subject = self.template_engine.render_template(template.subject_template, lead_data)
            body = self.template_engine.render_template(template.body_template, lead_data)
            
            # AI enhancement if enabled
            if template.use_ai_enhancement:
                enhanced_body = await self._enhance_with_ai(
                    body, lead, template.ai_tone, template.ai_length
                )
                body = enhanced_body
            
            # Create auto-response record
            auto_response = AutoResponse(
                lead_id=lead_id,
                template_id=template.id,
                subject=subject,
                body=body,
                personalization_data=lead_data,
                delay_minutes=delay_minutes,
                scheduled_at=datetime.utcnow() + timedelta(minutes=delay_minutes) if delay_minutes > 0 else None
            )
            
            self.db.add(auto_response)
            self.db.commit()
            self.db.refresh(auto_response)
            
            logger.info(f"Created auto-response {auto_response.id} for lead {lead_id}")
            
            # Schedule for sending if no delay
            if delay_minutes == 0:
                await self._send_auto_response(auto_response.id)
            
            return auto_response
            
        except Exception as e:
            logger.error(f"Failed to create auto-response for lead {lead_id}: {e}")
            self.db.rollback()
            raise
    
    async def _enhance_with_ai(
        self, 
        base_content: str, 
        lead: Lead, 
        tone: str, 
        length: str
    ) -> str:
        """Enhance response content with AI."""
        try:
            max_length = {"short": 200, "medium": 500, "long": 1000}.get(length, 500)
            
            prompt = f"""
            Enhance this email response to make it more personalized and engaging:
            
            Original message: {base_content}
            
            Lead details:
            - Title: {lead.title}
            - Description: {lead.description[:200] if lead.description else 'N/A'}
            - Category: {lead.category}
            - Location: {lead.location.name if lead.location else 'N/A'}
            - Price: ${lead.price if lead.price else 'N/A'}
            
            Requirements:
            - Keep the core message intact
            - Add specific references to their posting
            - Make it feel personal and human
            - Maintain {tone} tone
            - Include a clear next step
            """
            
            enhanced_content = await self.ai_provider.generate_response(
                prompt, tone, max_length
            )
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return base_content  # Return original on error
    
    async def _send_auto_response(self, response_id: int) -> bool:
        """Send an auto-response via email."""
        try:
            response = self.db.query(AutoResponse).filter(
                AutoResponse.id == response_id
            ).first()
            
            if not response:
                logger.error(f"Auto-response {response_id} not found")
                return False
            
            if response.status != "pending":
                logger.warning(f"Auto-response {response_id} already processed")
                return False
            
            lead = response.lead
            if not lead.email:
                logger.warning(f"No email address for lead {lead.id}")
                response.status = "failed"
                response.error_message = "No email address available"
                self.db.commit()
                return False
            
            # Send email (integrate with your email service)
            success = await self._send_email(
                to_email=lead.email,
                subject=response.subject,
                body=response.body,
                lead=lead
            )
            
            if success:
                response.status = "sent"
                response.sent_at = datetime.utcnow()
                
                # Record template usage for A/B testing
                self.ab_testing.record_template_usage(response.template_id, "sent")
                
                # Create notification
                await self._create_response_notification(response)
                
            else:
                response.status = "failed"
                response.retry_count += 1
                
                # Schedule retry if under max retries
                if response.retry_count < response.max_retries:
                    response.scheduled_at = datetime.utcnow() + timedelta(minutes=30)
                    response.status = "pending"
            
            self.db.commit()
            return success
            
        except Exception as e:
            logger.error(f"Failed to send auto-response {response_id}: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, body: str, lead: Lead) -> bool:
        """Send email via configured email service."""
        try:
            # This would integrate with your email service (SMTP, SendGrid, etc.)
            # For now, we'll simulate the email sending
            
            logger.info(f"Sending email to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {body[:100]}...")
            
            # TODO: Implement actual email sending
            # Example with SMTP:
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            
            await asyncio.sleep(0.1)  # Simulate email sending delay
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    async def _create_response_notification(self, response: AutoResponse):
        """Create notification for sent auto-response."""
        try:
            notification = Notification(
                notification_type="auto_response_sent",
                priority="normal",
                title=f"Auto-response sent to {response.lead.contact_name or 'lead'}",
                message=f"Successfully sent auto-response for lead '{response.lead.title}'",
                source_type="auto_response",
                source_id=response.id,
                channels=["websocket", "email"],
                data={
                    "lead_id": response.lead_id,
                    "response_id": response.id,
                    "template_id": response.template_id
                }
            )
            
            self.db.add(notification)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create response notification: {e}")
    
    async def process_pending_responses(self):
        """Process all pending auto-responses."""
        try:
            pending_responses = self.db.query(AutoResponse).filter(
                and_(
                    AutoResponse.status == "pending",
                    or_(
                        AutoResponse.scheduled_at.is_(None),
                        AutoResponse.scheduled_at <= datetime.utcnow()
                    )
                )
            ).all()
            
            logger.info(f"Processing {len(pending_responses)} pending auto-responses")
            
            for response in pending_responses:
                try:
                    await self._send_auto_response(response.id)
                    # Add delay between sends to appear more human
                    await asyncio.sleep(random.uniform(1, 5))
                except Exception as e:
                    logger.error(f"Failed to process response {response.id}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to process pending responses: {e}")
    
    async def track_response_engagement(
        self, 
        response_id: int, 
        event_type: str, 
        event_data: Optional[Dict] = None
    ):
        """Track engagement events (email opens, clicks, replies)."""
        try:
            response = self.db.query(AutoResponse).filter(
                AutoResponse.id == response_id
            ).first()
            
            if not response:
                return
            
            if event_type == "email_opened":
                response.email_opened = True
            elif event_type == "email_clicked":
                response.email_clicked = True
            elif event_type == "lead_responded":
                response.lead_responded = True
                response.response_received_at = datetime.utcnow()
                
                # Record conversion for A/B testing
                self.ab_testing.record_template_usage(response.template_id, "response")
            
            self.db.commit()
            
            logger.info(f"Tracked {event_type} for response {response_id}")
            
        except Exception as e:
            logger.error(f"Failed to track engagement for response {response_id}: {e}")
    
    def get_response_analytics(self, days: int = 30) -> Dict:
        """Get auto-response performance analytics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get overall stats
            total_responses = self.db.query(AutoResponse).filter(
                AutoResponse.created_at >= cutoff_date
            ).count()
            
            sent_responses = self.db.query(AutoResponse).filter(
                and_(
                    AutoResponse.created_at >= cutoff_date,
                    AutoResponse.status == "sent"
                )
            ).count()
            
            opened_responses = self.db.query(AutoResponse).filter(
                and_(
                    AutoResponse.created_at >= cutoff_date,
                    AutoResponse.email_opened == True
                )
            ).count()
            
            clicked_responses = self.db.query(AutoResponse).filter(
                and_(
                    AutoResponse.created_at >= cutoff_date,
                    AutoResponse.email_clicked == True
                )
            ).count()
            
            replied_responses = self.db.query(AutoResponse).filter(
                and_(
                    AutoResponse.created_at >= cutoff_date,
                    AutoResponse.lead_responded == True
                )
            ).count()
            
            return {
                "total_responses": total_responses,
                "sent_responses": sent_responses,
                "send_rate": (sent_responses / total_responses * 100) if total_responses > 0 else 0,
                "open_rate": (opened_responses / sent_responses * 100) if sent_responses > 0 else 0,
                "click_rate": (clicked_responses / sent_responses * 100) if sent_responses > 0 else 0,
                "reply_rate": (replied_responses / sent_responses * 100) if sent_responses > 0 else 0,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get response analytics: {e}")
            return {}


# Global service instance
auto_responder_service = AutoResponderService()