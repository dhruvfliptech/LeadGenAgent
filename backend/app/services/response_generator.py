"""
AI-powered Response Generation Service.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.leads import Lead
from app.models.response_templates import ResponseTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Service for generating personalized responses for leads."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_profile = {}  # Will be loaded from settings/database
        
    async def load_user_profile(self, user_id: Optional[int] = None) -> Dict:
        """
        Load user profile for personalizing responses.

        IMPORTANT: Requires USER_NAME and USER_EMAIL to be set in environment variables.
        Will not use fake/placeholder data to avoid professional embarrassment.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Check if required fields are configured
        if not settings.USER_NAME or not settings.USER_EMAIL:
            logger.error(
                "USER_NAME and USER_EMAIL must be set in .env file before generating responses. "
                "Will not use fake placeholder data (e.g., 'John Doe', '555-0100')."
            )
            # Return empty profile - response generation should handle this gracefully
            self.user_profile = {
                'user_name': '',
                'user_email': '',
                'user_phone': '',
                'configured': False
            }
            return self.user_profile

        # Use real configured values only
        self.user_profile = {
            'user_name': settings.USER_NAME,
            'user_email': settings.USER_EMAIL,
            'user_phone': settings.USER_PHONE or '',
            'configured': True,
            # Optional fields - can be extended via environment variables
            'user_profession': getattr(settings, 'USER_PROFESSION', ''),
            'years_experience': getattr(settings, 'USER_YEARS_EXPERIENCE', ''),
            'relevant_skills': getattr(settings, 'USER_SKILLS', ''),
            'portfolio_url': getattr(settings, 'USER_PORTFOLIO_URL', ''),
            'linkedin_url': getattr(settings, 'USER_LINKEDIN_URL', ''),
            'github_url': getattr(settings, 'USER_GITHUB_URL', ''),
        }

        logger.info(f"User profile loaded for: {self.user_profile['user_name']}")
        return self.user_profile
    
    async def generate_response(
        self,
        lead: Lead,
        template: Optional[ResponseTemplate] = None,
        use_ai: bool = True,
        custom_variables: Optional[Dict] = None
    ) -> Tuple[str, str, Dict]:
        """
        Generate a personalized response for a lead.
        
        Returns:
            Tuple of (subject, body, metadata)
        """
        # Load user profile if not loaded
        if not self.user_profile:
            await self.load_user_profile()
        
        # Get or create template
        if not template:
            template = await self._select_best_template(lead)
        
        # Extract variables from lead
        lead_variables = self._extract_lead_variables(lead)
        
        # Merge all variables
        variables = {
            **self.user_profile,
            **lead_variables,
            **(custom_variables or {})
        }
        
        # Process template
        subject = self._process_template(template.subject or "", variables) if template.subject else f"Re: {lead.title}"
        body = self._process_template(template.body, variables)
        
        # Enhance with AI if enabled
        if use_ai and template.use_ai_enhancement and settings.OPENAI_API_KEY:
            enhanced_body = await self._enhance_with_ai(body, lead, template)
            if enhanced_body:
                body = enhanced_body
        
        # Track usage
        template.times_used = (template.times_used or 0) + 1
        
        metadata = {
            'template_id': template.id,
            'template_name': template.name,
            'variables_used': list(variables.keys()),
            'ai_enhanced': use_ai and template.use_ai_enhancement,
            'generated_at': datetime.now().isoformat()
        }
        
        return subject, body, metadata
    
    def _extract_lead_variables(self, lead: Lead) -> Dict:
        """Extract variables from lead data."""
        variables = {
            'job_title': lead.title or 'the position',
            'company_name': self._extract_company_name(lead),
            'contact_name': lead.contact_name or lead.reply_contact_name,
            'compensation': lead.compensation,
            'location': 'your location',  # Skip location relationship for now
            'neighborhood': lead.neighborhood,
            'is_remote': lead.is_remote,
            'employment_type': ', '.join(lead.employment_type) if lead.employment_type else 'full-time',
            'posting_date': lead.posted_at.strftime('%B %d') if lead.posted_at else 'recently',
            'listing_url': lead.url
        }
        
        # Extract key requirements from description
        if lead.description:
            variables['key_requirements'] = self._extract_key_requirements(lead.description)
            variables['key_qualification'] = self._extract_key_qualification(lead.description)
        
        # Determine project or team
        if 'team' in (lead.title or '').lower() or 'team' in (lead.description or '').lower():
            variables['project_or_team'] = 'team'
        else:
            variables['project_or_team'] = 'project'
        
        return variables
    
    def _extract_company_name(self, lead: Lead) -> Optional[str]:
        """Try to extract company name from lead data."""
        # Look in attributes
        if lead.attributes and isinstance(lead.attributes, dict):
            if 'company' in lead.attributes:
                return lead.attributes['company']
        
        # Try to extract from title or description
        # This is a simplified version - could use NER in production
        return None
    
    def _extract_key_requirements(self, description: str) -> str:
        """Extract key requirements from job description."""
        # Look for requirement patterns
        patterns = [
            r'requirements?:(.+?)(?:\n\n|$)',
            r'must have:(.+?)(?:\n\n|$)',
            r'qualifications?:(.+?)(?:\n\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower(), re.DOTALL)
            if match:
                requirements = match.group(1).strip()
                # Get first 3 requirements
                lines = requirements.split('\n')[:3]
                return ', '.join(line.strip('•-* ') for line in lines if line.strip())
        
        # Fallback: extract skills mentioned
        skills = re.findall(r'\b(?:Python|JavaScript|Java|React|Node|AWS|Docker|SQL)\b', description, re.I)
        if skills:
            return ', '.join(set(skills[:3]))
        
        return 'the requirements mentioned'
    
    def _extract_key_qualification(self, description: str) -> str:
        """Extract the most important qualification from description."""
        # This is simplified - in production would use NLP
        skills = re.findall(r'\b(?:Python|JavaScript|Java|React|Node|AWS|Docker|SQL|TypeScript)\b', description, re.I)
        if skills:
            return skills[0]
        return 'relevant technical skills'
    
    def _process_template(self, template_text: str, variables: Dict) -> str:
        """Process template with variable substitution and conditionals."""
        result = template_text
        
        # Process conditionals {{if variable}} ... {{endif}}
        conditional_pattern = r'\{\{if\s+(\w+)\}\}(.*?)\{\{endif\}\}'
        
        def process_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            if variables.get(var_name):
                return content
            return ''
        
        result = re.sub(conditional_pattern, process_conditional, result, flags=re.DOTALL)
        
        # Process variables with defaults {{variable|default}}
        variable_pattern = r'\{\{(\w+)(?:\|([^}]+))?\}\}'
        
        def process_variable(match):
            var_name = match.group(1)
            default = match.group(2) if match.group(2) else ''
            return str(variables.get(var_name, default))
        
        result = re.sub(variable_pattern, process_variable, result)
        
        # Clean up extra whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    async def _select_best_template(self, lead: Lead) -> ResponseTemplate:
        """Select the best template for a lead based on context."""
        # Try to find a matching template type
        template_type = 'general'
        
        if 'job' in lead.category.lower() if lead.category else False:
            template_type = 'job_application'
        elif 'gig' in lead.category.lower() if lead.category else False:
            template_type = 'gig_inquiry'
        
        # Query for active template of this type
        # Order by response_count/sent_count ratio (success rate)
        query = select(ResponseTemplate).where(
            ResponseTemplate.category == template_type,
            ResponseTemplate.is_active == True
        ).order_by(ResponseTemplate.response_count.desc()).limit(1)
        
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            # Create a default template
            template = await self._create_default_template(template_type)
        
        return template
    
    async def _create_default_template(self, template_type: str) -> ResponseTemplate:
        """Create a default template if none exists."""
        template = ResponseTemplate(
            name=f"Default {template_type.replace('_', ' ').title()} Template",
            description=f"Default template for {template_type}",
            category=template_type,
            subject_template="Interested in {{job_title}} Position",
            body_template="""Hi {{contact_name|there}},

I noticed your posting for {{job_title}} and I'm very interested in learning more about this opportunity.

I have {{years_experience}} years of experience in {{relevant_skills}}, which aligns well with what you're looking for.

{{if compensation}}
The compensation range of {{compensation}} fits within my expectations.
{{endif}}

{{if is_remote}}
I'm set up for remote work and have successfully worked remotely in similar positions.
{{endif}}

I'd appreciate the opportunity to discuss how my background can contribute to {{project_or_team}}.

I'm available for a conversation at your convenience. {{availability_statement}}

Best regards,
{{user_name}}
{{user_email}}
{{if user_phone}}
{{user_phone}}
{{endif}}""",
            required_variables=['job_title', 'user_name', 'user_email'],
            optional_variables=['contact_name', 'compensation', 'company_name', 'user_phone'],
            tone='professional',
            length='medium'
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def _enhance_with_ai(self, base_response: str, lead: Lead, template: ResponseTemplate) -> Optional[str]:
        """Enhance response using AI (OpenAI/Claude)."""
        # This would integrate with OpenAI API
        # For now, return None to use base response
        return None
    
    async def batch_generate_responses(
        self,
        leads: List[Lead],
        template: Optional[ResponseTemplate] = None,
        use_ai: bool = True
    ) -> List[Dict]:
        """Generate responses for multiple leads."""
        results = []
        
        for lead in leads:
            try:
                subject, body, metadata = await self.generate_response(
                    lead, template, use_ai
                )
                
                # Store generated response in lead
                if not lead.generated_responses:
                    lead.generated_responses = []
                
                lead.generated_responses.append({
                    'subject': subject,
                    'body': body,
                    'metadata': metadata,
                    'generated_at': datetime.now().isoformat()
                })
                
                results.append({
                    'lead_id': lead.id,
                    'craigslist_id': lead.craigslist_id,
                    'subject': subject,
                    'body': body,
                    'metadata': metadata,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Error generating response for lead {lead.id}: {str(e)}")
                results.append({
                    'lead_id': lead.id,
                    'error': str(e),
                    'success': False
                })
        
        await self.db.commit()
        return results
    
    async def test_template(
        self,
        template: ResponseTemplate,
        sample_lead: Optional[Lead] = None
    ) -> Dict:
        """Test a template with sample data."""
        # Create sample lead if not provided
        if not sample_lead:
            sample_lead = Lead(
                craigslist_id='sample_123',
                title='Senior Software Engineer - Python/React',
                description='We are looking for a senior software engineer with Python and React experience.',
                compensation='$130,000 - $160,000',
                employment_type=['full-time'],
                is_remote=True,
                location_id=1,
                posted_at=datetime.now()
            )
        
        # Generate response
        subject, body, metadata = await self.generate_response(
            sample_lead, template, use_ai=False
        )
        
        return {
            'template_id': template.id,
            'template_name': template.name,
            'sample_output': {
                'subject': subject,
                'body': body
            },
            'metadata': metadata,
            'variables_available': list(self.user_profile.keys()) + [
                'job_title', 'company_name', 'contact_name', 'compensation',
                'location', 'is_remote', 'employment_type'
            ]
        }