"""
AI-Powered Demo Site Generator

This service uses OpenRouter AI to generate personalized demo sites.
Supports multiple AI models (GPT-4, Claude, etc.) for HTML/CSS/JS generation.
"""

import os
import re
from typing import Dict, Any, Optional, List
from jinja2 import Template, Environment, BaseLoader
import logging

from app.services.openrouter_client import OpenRouterClient
from app.models.demo_sites import DemoSiteTemplate

logger = logging.getLogger(__name__)


class SiteGenerator:
    """
    AI-powered demo site generator.

    Uses OpenRouter to generate complete HTML/CSS/JS based on
    templates and personalization data.
    """

    def __init__(self):
        """Initialize the site generator with AI client."""
        self.ai_client = OpenRouterClient()
        self.jinja_env = Environment(loader=BaseLoader())

    async def generate_site(
        self,
        template: DemoSiteTemplate,
        content_data: Dict[str, Any],
        style_settings: Dict[str, Any],
        ai_model: str = "gpt-4",
        use_ai: bool = True
    ) -> Dict[str, str]:
        """
        Generate a complete demo site.

        Args:
            template: The template to use
            content_data: Personalized content data
            style_settings: Style customization settings
            ai_model: AI model to use for generation
            use_ai: Whether to use AI for content enhancement

        Returns:
            Dict with 'html', 'css', 'js' keys containing generated code
        """
        try:
            # First, render the template with content data
            rendered = self._render_template(template, content_data, style_settings)

            # If AI enhancement is enabled, enhance the content
            if use_ai:
                enhanced = await self._enhance_with_ai(
                    rendered,
                    content_data,
                    style_settings,
                    ai_model
                )
                return enhanced

            return rendered

        except Exception as e:
            logger.error(f"Site generation failed: {str(e)}")
            raise

    def _render_template(
        self,
        template: DemoSiteTemplate,
        content_data: Dict[str, Any],
        style_settings: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render the template with content and style data.

        Uses Jinja2 to replace variables in the template.
        """
        try:
            # Prepare template variables
            template_vars = {
                **content_data,
                'style': style_settings,
                'primary_color': style_settings.get('primary_color', '#3B82F6'),
                'secondary_color': style_settings.get('secondary_color', '#1E40AF'),
                'accent_color': style_settings.get('accent_color', '#F59E0B'),
                'font_family': style_settings.get('font_family', 'Inter, sans-serif'),
            }

            # Render HTML
            html_template = self.jinja_env.from_string(template.html_template)
            rendered_html = html_template.render(**template_vars)

            # Render CSS
            css_template = self.jinja_env.from_string(template.css_template)
            rendered_css = css_template.render(**template_vars)

            # Render JS (if present)
            rendered_js = ""
            if template.js_template:
                js_template = self.jinja_env.from_string(template.js_template)
                rendered_js = js_template.render(**template_vars)

            return {
                'html': rendered_html,
                'css': rendered_css,
                'js': rendered_js
            }

        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            raise

    async def _enhance_with_ai(
        self,
        rendered: Dict[str, str],
        content_data: Dict[str, Any],
        style_settings: Dict[str, Any],
        ai_model: str
    ) -> Dict[str, str]:
        """
        Enhance the rendered site with AI-generated improvements.

        AI can improve:
        - Copy and headlines
        - Meta descriptions
        - Call-to-action text
        - Feature descriptions
        """
        try:
            # Build enhancement prompt
            prompt = self._build_enhancement_prompt(rendered, content_data)

            # Call AI to enhance
            response = await self.ai_client.generate_completion(
                model=ai_model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )

            # Parse AI response and apply enhancements
            enhanced = self._apply_ai_enhancements(rendered, response)

            return enhanced

        except Exception as e:
            logger.warning(f"AI enhancement failed, using original: {str(e)}")
            return rendered

    def _build_enhancement_prompt(
        self,
        rendered: Dict[str, str],
        content_data: Dict[str, Any]
    ) -> str:
        """Build the prompt for AI enhancement."""
        lead_name = content_data.get('lead_name', 'the user')
        company_name = content_data.get('company_name', 'their company')
        industry = content_data.get('industry', 'their industry')

        prompt = f"""
You are a professional copywriter creating a personalized demo website.

CONTEXT:
- Lead Name: {lead_name}
- Company: {company_name}
- Industry: {industry}

CURRENT CONTENT:
{rendered.get('html', '')[:1000]}...

TASK:
Enhance the following elements to be more personalized and compelling:
1. Headline (make it attention-grabbing and relevant to {company_name})
2. Subheadline (clearly state the value proposition)
3. Call-to-action text (action-oriented, specific to the industry)
4. Feature descriptions (benefit-focused, industry-specific)

REQUIREMENTS:
- Keep it professional and concise
- Use the lead's name and company naturally
- Focus on benefits, not features
- Make CTAs action-oriented
- Keep formatting simple (plain text)

Return your enhancements in this JSON format:
{{
    "headline": "Your enhanced headline",
    "subheadline": "Your enhanced subheadline",
    "cta_text": "Your enhanced CTA",
    "features": ["Feature 1 description", "Feature 2 description", "Feature 3 description"]
}}
"""
        return prompt

    def _apply_ai_enhancements(
        self,
        rendered: Dict[str, str],
        ai_response: str
    ) -> Dict[str, str]:
        """Apply AI enhancements to the rendered site."""
        try:
            # Extract JSON from AI response
            import json
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                enhancements = json.loads(json_match.group())

                # Apply enhancements to HTML
                html = rendered['html']

                if 'headline' in enhancements:
                    html = self._replace_placeholder(html, 'headline', enhancements['headline'])

                if 'subheadline' in enhancements:
                    html = self._replace_placeholder(html, 'subheadline', enhancements['subheadline'])

                if 'cta_text' in enhancements:
                    html = self._replace_placeholder(html, 'cta_text', enhancements['cta_text'])

                rendered['html'] = html

        except Exception as e:
            logger.warning(f"Failed to apply AI enhancements: {str(e)}")

        return rendered

    def _replace_placeholder(self, html: str, placeholder: str, value: str) -> str:
        """Replace a placeholder in the HTML with the new value."""
        # Try various placeholder formats
        patterns = [
            f"{{{{{placeholder}}}}}",  # {{placeholder}}
            f"{{{{ {placeholder} }}}}",  # {{ placeholder }}
            f"<span class=\"{placeholder}\">.*?</span>",  # <span class="placeholder">...</span>
            f"<h1[^>]*>.*?</h1>",  # <h1>...</h1> for headlines
        ]

        for pattern in patterns:
            if re.search(pattern, html):
                html = re.sub(pattern, value, html, count=1)
                break

        return html

    async def generate_from_scratch(
        self,
        content_data: Dict[str, Any],
        style_settings: Dict[str, Any],
        template_type: str = "landing",
        ai_model: str = "gpt-4"
    ) -> Dict[str, str]:
        """
        Generate a complete demo site from scratch using AI.

        This method doesn't use a template - AI creates everything.
        """
        try:
            prompt = self._build_generation_prompt(
                content_data,
                style_settings,
                template_type
            )

            response = await self.ai_client.generate_completion(
                model=ai_model,
                prompt=prompt,
                max_tokens=4000,
                temperature=0.8
            )

            # Parse HTML/CSS/JS from AI response
            generated = self._parse_generated_code(response)

            return generated

        except Exception as e:
            logger.error(f"AI generation from scratch failed: {str(e)}")
            raise

    def _build_generation_prompt(
        self,
        content_data: Dict[str, Any],
        style_settings: Dict[str, Any],
        template_type: str
    ) -> str:
        """Build prompt for AI to generate complete site from scratch."""
        lead_name = content_data.get('lead_name', 'User')
        company_name = content_data.get('company_name', 'Your Company')
        industry = content_data.get('industry', 'technology')

        primary_color = style_settings.get('primary_color', '#3B82F6')
        secondary_color = style_settings.get('secondary_color', '#1E40AF')
        font_family = style_settings.get('font_family', 'Inter, sans-serif')

        prompt = f"""
You are an expert web developer creating a personalized {template_type} page.

REQUIREMENTS:
- Create a complete, modern, responsive HTML page
- Include inline CSS (no external stylesheets)
- Use vanilla JavaScript (no frameworks)
- Make it mobile-friendly (responsive design)
- Use modern CSS (flexbox, grid)
- Include meta tags for SEO

PERSONALIZATION:
- Lead Name: {lead_name}
- Company: {company_name}
- Industry: {industry}

DESIGN REQUIREMENTS:
- Primary Color: {primary_color}
- Secondary Color: {secondary_color}
- Font: {font_family}
- Clean, professional design
- Clear call-to-action

STRUCTURE (for {template_type} page):
{"- Hero section with headline and CTA" if template_type == "landing" else ""}
{"- Features section (3 features)" if template_type == "landing" else ""}
{"- Testimonials section" if template_type == "landing" else ""}
{"- Portfolio grid" if template_type == "portfolio" else ""}
{"- Pricing table" if template_type == "saas" else ""}
- Footer with contact info

CRITICAL: Return ONLY the HTML code, starting with <!DOCTYPE html>. Include CSS in <style> tag and JS in <script> tag.
Do NOT include explanations, markdown formatting, or code fences.
"""
        return prompt

    def _parse_generated_code(self, ai_response: str) -> Dict[str, str]:
        """Parse HTML/CSS/JS from AI-generated response."""
        # Extract HTML (everything from <!DOCTYPE to </html>)
        html_match = re.search(
            r'<!DOCTYPE html>.*</html>',
            ai_response,
            re.DOTALL | re.IGNORECASE
        )

        if html_match:
            full_html = html_match.group()

            # Extract CSS from <style> tags
            css_match = re.search(
                r'<style[^>]*>(.*?)</style>',
                full_html,
                re.DOTALL | re.IGNORECASE
            )
            css = css_match.group(1) if css_match else ""

            # Extract JS from <script> tags
            js_match = re.search(
                r'<script[^>]*>(.*?)</script>',
                full_html,
                re.DOTALL | re.IGNORECASE
            )
            js = js_match.group(1) if js_match else ""

            return {
                'html': full_html,
                'css': css,
                'js': js
            }

        # Fallback: return basic HTML if parsing fails
        return {
            'html': ai_response if '<!DOCTYPE' in ai_response else f'<!DOCTYPE html><html><body>{ai_response}</body></html>',
            'css': '',
            'js': ''
        }

    def validate_generated_code(self, generated: Dict[str, str]) -> bool:
        """
        Validate that generated code is safe and well-formed.

        Checks for:
        - Valid HTML structure
        - No malicious scripts
        - Reasonable file sizes
        """
        try:
            html = generated.get('html', '')

            # Check basic HTML structure
            if not html.startswith('<!DOCTYPE') and '<html' not in html:
                return False

            # Check for malicious patterns
            malicious_patterns = [
                r'<script[^>]*src=["\']https?://',  # External scripts
                r'eval\(',  # eval() calls
                r'Function\(',  # Function constructor
                r'<iframe',  # Iframes
            ]

            for pattern in malicious_patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    logger.warning(f"Malicious pattern detected: {pattern}")
                    return False

            # Check file size (max 500KB)
            if len(html) > 500000:
                logger.warning("Generated HTML exceeds size limit")
                return False

            return True

        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
