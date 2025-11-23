
# Demo Site Builder - Complete Implementation Guide

## Overview

The Demo Site Builder is an AI-powered system for generating personalized demo websites for leads. It features template-based generation, AI content personalization, automatic Vercel deployment, and comprehensive analytics tracking.

## Architecture

### Core Components

1. **Site Generator** (`site_generator.py`)
   - AI-powered HTML/CSS/JS generation
   - Template-based rendering with Jinja2
   - Code validation and security checks
   - Supports multiple AI models (GPT-4, Claude, etc.)

2. **Template Engine** (`template_engine.py`)
   - Jinja2 template rendering
   - Style customization and color schemes
   - Mobile optimization
   - Analytics injection

3. **Vercel Deployer** (`vercel_deployer.py`)
   - Automatic deployment to Vercel
   - Custom subdomain generation
   - SSL certificate management
   - Deployment status tracking

4. **Analytics Tracker** (`analytics_tracker.py`)
   - Privacy-friendly visitor tracking
   - Daily metrics aggregation
   - Conversion tracking
   - Device and referrer analytics

5. **Content Personalizer** (`content_personalizer.py`)
   - AI-powered content generation
   - Lead-specific personalization
   - SEO meta tag generation
   - Industry-specific copy

### Database Schema

**demo_sites** (enhanced):
- `id`, `lead_id`, `template_id`
- `site_name`, `project_name` (subdomain)
- `content_data` (JSON), `style_settings` (JSON)
- `generated_html`, `generated_css`, `generated_js`
- `status` (draft/building/deployed/failed)
- `vercel_deployment_id`, `vercel_url`
- `analytics_enabled`, `total_views`, `total_conversions`
- `created_at`, `updated_at`, `last_deployed_at`

**demo_site_templates**:
- `id`, `template_name`, `template_type`
- `html_template`, `css_template`, `js_template`
- `customization_options` (JSON)
- `is_active`, `is_default`, `usage_count`
- SEO fields (`default_meta_title`, etc.)

**demo_site_analytics**:
- `id`, `demo_site_id`, `date`
- `page_views`, `unique_visitors`
- `avg_time_on_page`, `bounce_rate`
- `cta_clicks`, `conversions`, `conversion_rate`
- `analytics_data` (JSON) - detailed metrics

**demo_site_components**:
- `id`, `component_name`, `component_type`
- `html_code`, `css_code`, `js_code`
- `category`, `tags` (JSON)
- `required_data_fields`, `optional_data_fields`

## Setup Instructions

### 1. Environment Variables

Add to your `.env` file:

```bash
# Vercel Deployment
VERCEL_API_TOKEN=your_vercel_api_token
VERCEL_TEAM_ID=your_team_id  # Optional
VERCEL_PROJECT_NAME=demo-sites
VERCEL_DOMAIN=yourdomain.com

# Demo Site Settings
DEMO_SITE_BASE_DOMAIN=demo.yourapp.com
DEMO_SITE_STORAGE_PATH=backend/storage/demo-sites
DEMO_SITE_ANALYTICS_ENABLED=true
DEMO_SITE_DEFAULT_TEMPLATE=landing-page

# OpenRouter AI (for generation)
OPENROUTER_API_KEY=your_openrouter_key
```

### 2. Database Migration

Run the migration to create all tables:

```bash
cd backend
alembic upgrade head
```

### 3. Seed Templates

Load the 3 pre-built templates:

```bash
python -m scripts.seed_demo_templates
```

This creates:
- Modern Landing Page (default)
- Professional Portfolio
- SaaS Product Demo

### 4. Vercel Setup

1. Create a Vercel account at https://vercel.com
2. Generate an API token:
   - Go to Settings → Tokens
   - Create new token
   - Copy to `VERCEL_API_TOKEN`

3. (Optional) Create a team:
   - Copy team ID to `VERCEL_TEAM_ID`

4. Configure domain:
   - Add your domain in Vercel dashboard
   - Update `DEMO_SITE_BASE_DOMAIN`

## API Endpoints

### Demo Site Generation

#### POST /api/v1/demo-sites/generate
Generate a new demo site with AI.

**Request:**
```json
{
  "site_name": "Acme Corp Demo",
  "lead_id": 123,
  "template_type": "landing",
  "use_ai_generation": true,
  "ai_model": "gpt-4",
  "content_data": {
    "lead_name": "John Doe",
    "company_name": "Acme Corp",
    "industry": "technology",
    "headline": "Transform Your Business",
    "subheadline": "Next-gen solutions",
    "cta_text": "Get Started"
  },
  "style_settings": {
    "primary_color": "#3B82F6",
    "secondary_color": "#1E40AF",
    "accent_color": "#F59E0B",
    "font_family": "Inter, sans-serif"
  },
  "auto_deploy": true
}
```

**Response:**
```json
{
  "id": 1,
  "site_name": "Acme Corp Demo",
  "subdomain": "acme-corp-demo-1234567890",
  "deployment_status": "building",
  "vercel_url": null,
  "created_at": "2024-11-05T10:00:00Z"
}
```

#### GET /api/v1/demo-sites
List all demo sites with pagination and filtering.

**Query Params:**
- `page` (default: 1)
- `page_size` (default: 20)
- `status` (draft/building/deployed/failed)
- `lead_id` (filter by lead)
- `template_type` (landing/portfolio/saas)

#### GET /api/v1/demo-sites/{id}
Get demo site details.

#### PUT /api/v1/demo-sites/{id}
Update demo site configuration.

#### DELETE /api/v1/demo-sites/{id}
Delete demo site (soft delete).

#### POST /api/v1/demo-sites/{id}/deploy
Deploy demo site to Vercel.

#### GET /api/v1/demo-sites/{id}/preview
Get preview HTML/CSS/JS.

#### POST /api/v1/demo-sites/{id}/duplicate
Duplicate an existing demo site.

#### GET /api/v1/demo-sites/{id}/export
Export demo site files as JSON.

### Template Management

#### GET /api/v1/demo-sites/templates
List all available templates.

#### GET /api/v1/demo-sites/templates/{id}
Get template details.

#### POST /api/v1/demo-sites/templates
Create custom template.

**Request:**
```json
{
  "template_name": "My Custom Template",
  "template_type": "landing",
  "description": "Custom landing page",
  "html_template": "<html>...</html>",
  "css_template": "body { ... }",
  "js_template": "",
  "is_active": true
}
```

#### PUT /api/v1/demo-sites/templates/{id}
Update template.

#### DELETE /api/v1/demo-sites/templates/{id}
Delete template.

### Analytics

#### GET /api/v1/demo-sites/{id}/analytics/summary
Get analytics summary for date range.

**Query Params:**
- `days` (default: 30)

**Response:**
```json
{
  "demo_site_id": 1,
  "total_page_views": 1234,
  "total_unique_visitors": 456,
  "total_cta_clicks": 89,
  "total_conversions": 12,
  "overall_conversion_rate": 2.63,
  "avg_time_on_page": 45.2,
  "avg_bounce_rate": 35.8,
  "date_range": {
    "start": "2024-10-01",
    "end": "2024-11-01"
  }
}
```

#### GET /api/v1/demo-sites/{id}/analytics/timeline
Get daily analytics timeline.

#### POST /api/v1/demo-sites/{id}/analytics/track
Track analytics event (public endpoint).

**Request:**
```json
{
  "event_type": "page_view",
  "visitor_id": "visitor_abc123",
  "event_data": {
    "url": "https://demo.site.com",
    "referrer": "https://google.com",
    "screen": "1920x1080"
  }
}
```

### Components

#### GET /api/v1/demo-sites/components
List all available UI components.

#### GET /api/v1/demo-sites/components/{id}
Get component details.

#### POST /api/v1/demo-sites/components
Create new component.

#### PUT /api/v1/demo-sites/components/{id}
Update component.

## Template Creation Guide

### Template Structure

Templates use Jinja2 syntax with double braces for variables:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{company_name}} - {{headline}}</title>
    <meta name="description" content="{{meta_description}}">
</head>
<body>
    <h1>{{headline}}</h1>
    <p>{{subheadline}}</p>
    <button data-cta>{{cta_text}}</button>
</body>
</html>
```

### Available Variables

**Standard Variables:**
- `{{lead_name}}` - Lead's name
- `{{company_name}}` - Company name
- `{{industry}}` - Industry/vertical
- `{{headline}}` - Main headline
- `{{subheadline}}` - Supporting text
- `{{cta_text}}` - Call-to-action text
- `{{contact_email}}` - Contact email
- `{{contact_phone}}` - Contact phone

**Style Variables:**
- `{{primary_color}}` - Primary brand color
- `{{secondary_color}}` - Secondary color
- `{{accent_color}}` - Accent color
- `{{font_family}}` - Font family
- `{{border_radius}}` - Border radius

### CSS Best Practices

```css
/* Use CSS variables for colors */
:root {
    --primary-color: {{primary_color}};
    --secondary-color: {{secondary_color}};
    --accent-color: {{accent_color}};
}

/* Mobile-first responsive design */
body {
    font-family: {{font_family}};
    font-size: 16px;
}

@media (max-width: 768px) {
    body {
        font-size: 14px;
    }
}

/* Use semantic classes */
.cta-button {
    background: var(--primary-color);
    border-radius: {{border_radius}};
}
```

### Analytics Integration

Add `data-cta` attribute to track clicks:

```html
<button data-cta>{{cta_text}}</button>
<a href="#contact" data-cta>Contact Us</a>
```

The analytics script is automatically injected.

## AI Content Generation

### How It Works

1. **Template Selection**: Choose or AI selects appropriate template
2. **Lead Analysis**: Extract lead information (name, company, industry)
3. **AI Personalization**: Generate personalized copy using AI
4. **Template Rendering**: Render template with personalized content
5. **Code Validation**: Validate generated HTML/CSS/JS
6. **Mobile Optimization**: Add responsive CSS
7. **Analytics Injection**: Add tracking code

### AI Prompts

The system uses structured prompts for each template type:

**Landing Page Prompt:**
```
Create compelling landing page content for {company_name}
in the {industry} industry. Include:
- Attention-grabbing headline
- Clear value proposition
- 3 key features/benefits
- Strong call-to-action
```

**Portfolio Prompt:**
```
Create professional portfolio content for {lead_name}.
Include:
- Professional tagline
- About section
- 3 sample projects
- Skills list
- Contact CTA
```

**SaaS Prompt:**
```
Create SaaS product page for {company_name}.
Include:
- Product value headline
- 4 key features with benefits
- 3-tier pricing structure
- FAQ section
- Trial/demo CTA
```

### Customizing AI Generation

You can provide custom prompts:

```json
{
  "ai_prompt": "Create a landing page for an eco-friendly {industry} company that emphasizes sustainability and innovation."
}
```

## Vercel Deployment

### Deployment Process

1. **File Preparation**:
   - Generate index.html, styles.css, script.js
   - Add package.json for static site detection

2. **Project Creation**:
   - Sanitize project name (lowercase, alphanumeric, hyphens)
   - Create Vercel project via API

3. **File Upload**:
   - Upload files to Vercel
   - Set framework to "html" (static)

4. **Deployment**:
   - Trigger production deployment
   - Wait for build completion

5. **URL Generation**:
   - Get vercel.app subdomain
   - Optionally add custom domain

### Custom Domains

To add a custom domain:

```python
deployer = VercelDeployer()
await deployer.update_custom_domain(
    deployment_id="deployment_id",
    custom_domain="demo.yoursite.com"
)
```

Then add DNS records in your domain provider:
- Type: CNAME
- Name: demo
- Value: cname.vercel-dns.com

## Analytics Implementation

### Tracking Pixel

The analytics script is automatically injected into every demo site:

```javascript
// Tracks: page views, time on page, CTA clicks
(function() {
    const DEMO_SITE_ID = 123;
    const VISITOR_ID = localStorage.getItem('visitor_id');

    // Track page view
    fetch('/api/v1/demo-sites/123/analytics/track', {
        method: 'POST',
        body: JSON.stringify({
            event_type: 'page_view',
            visitor_id: VISITOR_ID,
            event_data: { url, referrer, screen }
        })
    });

    // Track CTA clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-cta]')) {
            // Track click event
        }
    });
})();
```

### Privacy-Friendly

- No cookies (uses localStorage)
- Anonymous visitor IDs
- No personal data collection
- GDPR compliant

### Metrics Collected

- **Page Views**: Total visits
- **Unique Visitors**: Distinct visitor IDs
- **Avg Time on Page**: Average session duration
- **Bounce Rate**: <5 second visits
- **CTA Clicks**: Clicks on tracked elements
- **Conversions**: Form submissions, sign-ups
- **Referrers**: Traffic sources
- **Devices**: Mobile/tablet/desktop

## Testing

### Run Full Test Suite

```bash
cd backend
pytest test_demo_site_builder.py -v
```

### Test Individual Components

```bash
# Test site generator
pytest test_demo_site_builder.py::test_site_generator_with_template -v

# Test template engine
pytest test_demo_site_builder.py::test_template_engine_rendering -v

# Test analytics
pytest test_demo_site_builder.py::test_analytics_tracker_track_event -v
```

### Integration Testing

```bash
# Test end-to-end generation
pytest test_demo_site_builder.py::test_end_to_end_site_generation -v
```

## Troubleshooting

### Common Issues

**1. Vercel Deployment Fails**
- Check `VERCEL_API_TOKEN` is valid
- Verify project name is unique
- Check Vercel account limits

**2. AI Generation Fails**
- Verify `OPENROUTER_API_KEY` is set
- Check AI model is available
- Review prompt length (max tokens)

**3. Analytics Not Tracking**
- Check analytics script is injected
- Verify endpoint is accessible (CORS)
- Check browser console for errors

**4. Template Rendering Fails**
- Validate Jinja2 syntax
- Check all required variables are provided
- Review template with `validate_template()`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### Caching

- Templates are cached in database
- Generated sites cached until modified
- Analytics aggregated daily

### Best Practices

1. **Limit Generated Code Size**: Max 500KB per site
2. **Optimize Images**: Use external CDN for images
3. **Minify CSS/JS**: Enable in production
4. **Use Edge Caching**: Leverage Vercel's CDN
5. **Batch Analytics**: Aggregate metrics daily

## Security

### Code Validation

All generated code is validated:
- No external script sources
- No eval() or Function() calls
- No iframes (unless explicitly allowed)
- Max file size limits

### XSS Prevention

- All user input escaped in templates
- Jinja2 autoescaping enabled
- Content Security Policy headers

### API Security

- All endpoints require authentication
- Rate limiting enabled
- CORS configured for demo sites only

## Monitoring

### Key Metrics

Monitor these metrics in production:

- Demo sites created per day
- AI generation success rate
- Vercel deployment success rate
- Average deployment time
- Total analytics events tracked
- Storage usage

### Alerts

Set up alerts for:
- Deployment failures (>10% failure rate)
- AI generation errors
- Analytics tracking failures
- Storage quota exceeded

## Roadmap

Future enhancements:

- [ ] A/B testing for demo sites
- [ ] Video background support
- [ ] Form builder integration
- [ ] Multi-page site support
- [ ] Custom subdomain per lead
- [ ] Advanced analytics (heatmaps)
- [ ] Template marketplace
- [ ] Collaboration features

## Support

For issues or questions:
1. Check this guide
2. Review test suite for examples
3. Check backend logs
4. Open GitHub issue

---

**Version**: 1.0.0
**Last Updated**: November 2024
**Author**: AI-Powered Demo Site Builder Team
