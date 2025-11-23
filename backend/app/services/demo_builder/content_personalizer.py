"""
Content Personalizer for Demo Sites

This service uses AI to personalize demo site content based on lead data.
Generates compelling copy, headlines, and CTAs tailored to each lead.
"""

from typing import Dict, Any, Optional, List
import logging

from app.services.openrouter_client import OpenRouterClient
from app.models.leads import Lead

logger = logging.getLogger(__name__)


class ContentPersonalizer:
    """
    AI-powered content personalization service.

    Creates personalized content for demo sites based on:
    - Lead profile (name, company, industry)
    - Template type
    - Business goals
    """

    def __init__(self):
        """Initialize content personalizer with AI client."""
        self.ai_client = OpenRouterClient()

    async def personalize_content(
        self,
        lead: Optional[Lead],
        template_type: str,
        base_content: Dict[str, Any],
        ai_model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Generate personalized content for a demo site.

        Args:
            lead: Lead object with profile data
            template_type: Type of template (landing, portfolio, saas)
            base_content: Base content to personalize
            ai_model: AI model to use

        Returns:
            Dict with personalized content
        """
        try:
            # Extract lead info
            lead_info = self._extract_lead_info(lead)

            # Generate personalized content based on template type
            if template_type == "landing":
                content = await self._personalize_landing_page(lead_info, base_content, ai_model)
            elif template_type == "portfolio":
                content = await self._personalize_portfolio(lead_info, base_content, ai_model)
            elif template_type == "saas":
                content = await self._personalize_saas_demo(lead_info, base_content, ai_model)
            else:
                content = await self._personalize_generic(lead_info, base_content, ai_model)

            return content

        except Exception as e:
            logger.error(f"Content personalization failed: {str(e)}")
            # Return base content if personalization fails
            return base_content

    def _extract_lead_info(self, lead: Optional[Lead]) -> Dict[str, Any]:
        """Extract relevant information from lead."""
        if not lead:
            return {
                'name': 'User',
                'company': 'Your Company',
                'industry': 'business',
                'location': None,
                'email': None
            }

        return {
            'name': lead.name or 'User',
            'company': getattr(lead, 'company', None) or 'Your Company',
            'industry': getattr(lead, 'industry', None) or 'business',
            'location': getattr(lead, 'location', None),
            'email': lead.email,
            'phone': lead.phone,
            'description': getattr(lead, 'description', None)
        }

    async def _personalize_landing_page(
        self,
        lead_info: Dict[str, Any],
        base_content: Dict[str, Any],
        ai_model: str
    ) -> Dict[str, Any]:
        """Personalize content for a landing page."""
        prompt = f"""
You are a professional copywriter creating a personalized landing page.

LEAD INFORMATION:
- Name: {lead_info['name']}
- Company: {lead_info['company']}
- Industry: {lead_info['industry']}
- Location: {lead_info.get('location', 'N/A')}

TASK:
Create compelling landing page content that:
1. Addresses {lead_info['company']}'s specific needs
2. Uses industry-specific language for {lead_info['industry']}
3. Creates urgency and value
4. Includes a clear call-to-action

Generate the following (return as JSON):
{{
    "headline": "Attention-grabbing headline (max 60 chars)",
    "subheadline": "Value proposition (max 120 chars)",
    "hero_text": "2-3 sentence description of value",
    "cta_text": "Action-oriented CTA button text",
    "cta_subtext": "Supporting text under CTA",
    "features": [
        {{"title": "Feature 1", "description": "Benefit-focused description"}},
        {{"title": "Feature 2", "description": "Benefit-focused description"}},
        {{"title": "Feature 3", "description": "Benefit-focused description"}}
    ],
    "testimonial": {{
        "quote": "Realistic testimonial quote",
        "author": "Similar company in {lead_info['industry']}"
    }}
}}

Requirements:
- Be specific to {lead_info['company']} and {lead_info['industry']}
- Focus on benefits, not features
- Use action verbs
- Keep it concise and impactful
- Make it sound natural, not salesy
"""

        response = await self.ai_client.generate_completion(
            model=ai_model,
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7
        )

        # Parse AI response
        content = self._parse_ai_json(response, base_content)

        # Add lead personalization
        content['lead_name'] = lead_info['name']
        content['company_name'] = lead_info['company']
        content['industry'] = lead_info['industry']

        return content

    async def _personalize_portfolio(
        self,
        lead_info: Dict[str, Any],
        base_content: Dict[str, Any],
        ai_model: str
    ) -> Dict[str, Any]:
        """Personalize content for a portfolio page."""
        prompt = f"""
Create personalized portfolio page content for {lead_info['company']}.

Industry: {lead_info['industry']}
Lead Name: {lead_info['name']}

Generate (return as JSON):
{{
    "headline": "Professional headline",
    "tagline": "Brief professional tagline",
    "about_text": "3-4 sentence about section",
    "projects": [
        {{"title": "Project 1", "description": "Brief description", "tech": ["tech1", "tech2"]}},
        {{"title": "Project 2", "description": "Brief description", "tech": ["tech1", "tech2"]}},
        {{"title": "Project 3", "description": "Brief description", "tech": ["tech1", "tech2"]}}
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
    "cta_text": "Contact or collaboration CTA"
}}

Make it relevant to {lead_info['industry']} industry.
"""

        response = await self.ai_client.generate_completion(
            model=ai_model,
            prompt=prompt,
            max_tokens=800,
            temperature=0.7
        )

        content = self._parse_ai_json(response, base_content)
        content['lead_name'] = lead_info['name']
        content['company_name'] = lead_info['company']

        return content

    async def _personalize_saas_demo(
        self,
        lead_info: Dict[str, Any],
        base_content: Dict[str, Any],
        ai_model: str
    ) -> Dict[str, Any]:
        """Personalize content for a SaaS demo page."""
        prompt = f"""
Create personalized SaaS demo page content for {lead_info['company']}.

Industry: {lead_info['industry']}
Target: {lead_info['name']}

Generate (return as JSON):
{{
    "headline": "Product value headline",
    "subheadline": "How it solves their problem",
    "features": [
        {{"icon": "⚡", "title": "Feature 1", "description": "Benefit"}},
        {{"icon": "🎯", "title": "Feature 2", "description": "Benefit"}},
        {{"icon": "📈", "title": "Feature 3", "description": "Benefit"}},
        {{"icon": "🔒", "title": "Feature 4", "description": "Benefit"}}
    ],
    "pricing_tiers": [
        {{"name": "Starter", "price": "$X/mo", "features": ["Feature 1", "Feature 2"]}},
        {{"name": "Professional", "price": "$X/mo", "features": ["All Starter", "Feature 3", "Feature 4"]}},
        {{"name": "Enterprise", "price": "Custom", "features": ["All Pro", "Feature 5", "Support"]}}
    ],
    "faq": [
        {{"question": "Common question 1?", "answer": "Answer"}},
        {{"question": "Common question 2?", "answer": "Answer"}},
        {{"question": "Common question 3?", "answer": "Answer"}}
    ],
    "cta_text": "Get Started / Book Demo"
}}

Tailor to {lead_info['industry']} industry needs.
"""

        response = await self.ai_client.generate_completion(
            model=ai_model,
            prompt=prompt,
            max_tokens=1200,
            temperature=0.7
        )

        content = self._parse_ai_json(response, base_content)
        content['lead_name'] = lead_info['name']
        content['company_name'] = lead_info['company']

        return content

    async def _personalize_generic(
        self,
        lead_info: Dict[str, Any],
        base_content: Dict[str, Any],
        ai_model: str
    ) -> Dict[str, Any]:
        """Personalize content for a generic template."""
        prompt = f"""
Create personalized website content for {lead_info['company']}.

Lead: {lead_info['name']}
Industry: {lead_info['industry']}

Generate (return as JSON):
{{
    "headline": "Main headline",
    "subheadline": "Supporting text",
    "body_text": "2-3 paragraphs of content",
    "cta_text": "Call to action"
}}

Make it relevant and compelling for their industry.
"""

        response = await self.ai_client.generate_completion(
            model=ai_model,
            prompt=prompt,
            max_tokens=600,
            temperature=0.7
        )

        content = self._parse_ai_json(response, base_content)
        content['lead_name'] = lead_info['name']
        content['company_name'] = lead_info['company']

        return content

    def _parse_ai_json(self, ai_response: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON from AI response, with fallback."""
        try:
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                return json.loads(json_match.group())

            # If no JSON found, return fallback
            return fallback

        except Exception as e:
            logger.warning(f"Failed to parse AI JSON: {str(e)}")
            return fallback

    async def generate_meta_tags(
        self,
        content: Dict[str, Any],
        template_type: str,
        ai_model: str = "gpt-4"
    ) -> Dict[str, str]:
        """
        Generate SEO meta tags for the demo site.

        Args:
            content: Personalized content
            template_type: Template type
            ai_model: AI model to use

        Returns:
            Dict with meta_title, meta_description, meta_keywords
        """
        try:
            headline = content.get('headline', 'Demo Site')
            company = content.get('company_name', 'Company')

            prompt = f"""
Generate SEO meta tags for a {template_type} page.

Headline: {headline}
Company: {company}

Return as JSON:
{{
    "meta_title": "60 char SEO title",
    "meta_description": "160 char description",
    "meta_keywords": "keyword1, keyword2, keyword3, keyword4, keyword5"
}}

Make it SEO-friendly and compelling for search results.
"""

            response = await self.ai_client.generate_completion(
                model=ai_model,
                prompt=prompt,
                max_tokens=200,
                temperature=0.5
            )

            meta_tags = self._parse_ai_json(response, {
                'meta_title': headline,
                'meta_description': f"Professional {template_type} page for {company}",
                'meta_keywords': template_type
            })

            return meta_tags

        except Exception as e:
            logger.error(f"Meta tag generation failed: {str(e)}")
            return {
                'meta_title': content.get('headline', 'Demo Site'),
                'meta_description': content.get('subheadline', 'Professional demo site'),
                'meta_keywords': template_type
            }

    def apply_personalization_to_template(
        self,
        template_html: str,
        personalized_content: Dict[str, Any]
    ) -> str:
        """
        Apply personalized content to a template.

        Replaces placeholders with personalized values.
        """
        try:
            html = template_html

            # Replace all content fields
            for key, value in personalized_content.items():
                if isinstance(value, str):
                    placeholder = f"{{{{{key}}}}}"
                    html = html.replace(placeholder, value)

            return html

        except Exception as e:
            logger.error(f"Template application failed: {str(e)}")
            return template_html
