"""
Seed script for demo site templates.

Creates 3 pre-built templates:
1. Landing Page Template
2. Portfolio Template
3. SaaS Demo Template

Run with: python -m scripts.seed_demo_templates
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session
from app.models.demo_sites import DemoSiteTemplate


# Template 1: Modern Landing Page
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{{meta_description}}">
    <title>{{headline}}</title>
</head>
<body>
    <!-- Hero Section -->
    <header class="hero">
        <nav class="navbar">
            <div class="container">
                <div class="logo">{{company_name}}</div>
                <div class="nav-links">
                    <a href="#features">Features</a>
                    <a href="#testimonials">Testimonials</a>
                    <a href="#contact">Contact</a>
                </div>
            </div>
        </nav>

        <div class="hero-content container">
            <h1>{{headline}}</h1>
            <p class="subheadline">{{subheadline}}</p>
            <button class="cta-button" data-cta>{{cta_text}}</button>
        </div>
    </header>

    <!-- Features Section -->
    <section id="features" class="features">
        <div class="container">
            <h2>Why Choose Us</h2>
            <div class="features-grid">
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <h3>Fast & Reliable</h3>
                    <p>Lightning-fast performance that your {{industry}} business can depend on.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🎯</div>
                    <h3>Results-Driven</h3>
                    <p>Proven strategies tailored specifically for {{company_name}}.</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📈</div>
                    <h3>Scalable Growth</h3>
                    <p>Grow your business with solutions that scale with you.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Testimonials -->
    <section id="testimonials" class="testimonials">
        <div class="container">
            <h2>What Our Clients Say</h2>
            <div class="testimonial-card">
                <p class="quote">"Working with them transformed our {{industry}} business. Highly recommend!"</p>
                <p class="author">- Industry Leader</p>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section id="contact" class="cta-section">
        <div class="container">
            <h2>Ready to Get Started, {{lead_name}}?</h2>
            <p>Join hundreds of {{industry}} companies that trust us</p>
            <button class="cta-button" data-cta>{{cta_text}}</button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {{company_name}}. All rights reserved.</p>
            <p>Contact: {{contact_email}}</p>
        </div>
    </footer>
</body>
</html>
"""

LANDING_PAGE_CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: {{font_family}};
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Navbar */
.navbar {
    background: white;
    padding: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: {{primary_color}};
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-links a {
    color: #333;
    text-decoration: none;
    transition: color 0.3s;
}

.nav-links a:hover {
    color: {{primary_color}};
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%);
    color: white;
    padding: 8rem 0 4rem;
    margin-top: 60px;
}

.hero-content {
    text-align: center;
    padding: 4rem 0;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.subheadline {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.cta-button {
    background: white;
    color: {{primary_color}};
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: {{border_radius}};
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
}

.cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* Features Section */
.features {
    padding: 4rem 0;
    background: #f8f9fa;
}

.features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: {{primary_color}};
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.feature {
    background: white;
    padding: 2rem;
    border-radius: {{border_radius}};
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.feature:hover {
    transform: translateY(-5px);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature h3 {
    color: {{primary_color}};
    margin-bottom: 1rem;
}

/* Testimonials */
.testimonials {
    padding: 4rem 0;
}

.testimonials h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: {{primary_color}};
}

.testimonial-card {
    background: white;
    padding: 3rem;
    border-radius: {{border_radius}};
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    max-width: 800px;
    margin: 0 auto;
}

.quote {
    font-size: 1.25rem;
    font-style: italic;
    margin-bottom: 1rem;
    color: #555;
}

.author {
    text-align: right;
    color: {{primary_color}};
    font-weight: bold;
}

/* CTA Section */
.cta-section {
    background: {{accent_color}};
    color: white;
    padding: 4rem 0;
    text-align: center;
}

.cta-section h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.cta-section .cta-button {
    background: white;
    color: {{accent_color}};
    margin-top: 2rem;
}

/* Footer */
.footer {
    background: #333;
    color: white;
    padding: 2rem 0;
    text-align: center;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .hero h1 {
        font-size: 2rem;
    }

    .nav-links {
        display: none;
    }

    .features-grid {
        grid-template-columns: 1fr;
    }
}
"""


# Template 2: Portfolio
PORTFOLIO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{lead_name}} - Portfolio</title>
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>{{lead_name}}</h1>
            <p class="tagline">{{tagline}}</p>
        </div>
    </header>

    <section class="about">
        <div class="container">
            <h2>About</h2>
            <p>{{about_text}}</p>
        </div>
    </section>

    <section class="projects">
        <div class="container">
            <h2>Featured Projects</h2>
            <div class="projects-grid">
                <div class="project-card">
                    <h3>Project Alpha</h3>
                    <p>Innovative solution for {{industry}}</p>
                    <div class="tech-stack">
                        <span class="tech-tag">Technology 1</span>
                        <span class="tech-tag">Technology 2</span>
                    </div>
                </div>
                <div class="project-card">
                    <h3>Project Beta</h3>
                    <p>Custom development for {{company_name}}</p>
                    <div class="tech-stack">
                        <span class="tech-tag">Technology 1</span>
                        <span class="tech-tag">Technology 2</span>
                    </div>
                </div>
                <div class="project-card">
                    <h3>Project Gamma</h3>
                    <p>Enterprise solution</p>
                    <div class="tech-stack">
                        <span class="tech-tag">Technology 1</span>
                        <span class="tech-tag">Technology 2</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="skills">
        <div class="container">
            <h2>Skills & Expertise</h2>
            <div class="skills-list">
                <span class="skill">Web Development</span>
                <span class="skill">UI/UX Design</span>
                <span class="skill">Cloud Solutions</span>
                <span class="skill">API Development</span>
                <span class="skill">Database Design</span>
            </div>
        </div>
    </section>

    <section class="contact">
        <div class="container">
            <h2>Get In Touch</h2>
            <p>{{cta_text}}</p>
            <button class="contact-button" data-cta>Contact Me</button>
        </div>
    </section>
</body>
</html>
"""

PORTFOLIO_CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: {{font_family}};
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: {{primary_color}};
    color: white;
    padding: 4rem 0;
    text-align: center;
}

.header h1 {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

.tagline {
    font-size: 1.25rem;
    opacity: 0.9;
}

section {
    padding: 4rem 0;
}

h2 {
    font-size: 2.5rem;
    margin-bottom: 2rem;
    color: {{primary_color}};
}

.about {
    background: #f8f9fa;
}

.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.project-card {
    background: white;
    padding: 2rem;
    border-radius: {{border_radius}};
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.project-card:hover {
    transform: translateY(-5px);
}

.project-card h3 {
    color: {{primary_color}};
    margin-bottom: 1rem;
}

.tech-stack {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.tech-tag {
    background: {{secondary_color}};
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
}

.skills {
    background: #f8f9fa;
}

.skills-list {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.skill {
    background: white;
    padding: 0.75rem 1.5rem;
    border-radius: {{border_radius}};
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid {{primary_color}};
}

.contact {
    text-align: center;
    background: {{accent_color}};
    color: white;
}

.contact h2 {
    color: white;
}

.contact-button {
    background: white;
    color: {{accent_color}};
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: {{border_radius}};
    cursor: pointer;
    margin-top: 2rem;
    transition: transform 0.2s;
}

.contact-button:hover {
    transform: scale(1.05);
}

@media (max-width: 768px) {
    .header h1 {
        font-size: 2rem;
    }

    .projects-grid {
        grid-template-columns: 1fr;
    }
}
"""


# Template 3: SaaS Demo
SAAS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{company_name}} - {{headline}}</title>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="logo">{{company_name}}</div>
            <div class="nav-menu">
                <a href="#features">Features</a>
                <a href="#pricing">Pricing</a>
                <a href="#faq">FAQ</a>
                <button class="nav-cta" data-cta>Get Started</button>
            </div>
        </div>
    </nav>

    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <h1>{{headline}}</h1>
                <p>{{subheadline}}</p>
                <button class="cta-primary" data-cta>Start Free Trial</button>
                <p class="cta-note">No credit card required</p>
            </div>
            <div class="hero-image">
                <div class="mockup">📊 Dashboard Preview</div>
            </div>
        </div>
    </section>

    <section id="features" class="features">
        <div class="container">
            <h2>Powerful Features for {{industry}}</h2>
            <div class="features-grid">
                <div class="feature-box">
                    <div class="feature-icon">⚡</div>
                    <h3>Lightning Fast</h3>
                    <p>Optimize your {{industry}} workflows with blazing speed</p>
                </div>
                <div class="feature-box">
                    <div class="feature-icon">🎯</div>
                    <h3>Precision Tools</h3>
                    <p>Built specifically for {{company_name}}'s needs</p>
                </div>
                <div class="feature-box">
                    <div class="feature-icon">📈</div>
                    <h3>Analytics</h3>
                    <p>Track performance and grow your business</p>
                </div>
                <div class="feature-box">
                    <div class="feature-icon">🔒</div>
                    <h3>Enterprise Security</h3>
                    <p>Bank-level encryption and compliance</p>
                </div>
            </div>
        </div>
    </section>

    <section id="pricing" class="pricing">
        <div class="container">
            <h2>Simple, Transparent Pricing</h2>
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3>Starter</h3>
                    <div class="price">$49<span>/month</span></div>
                    <ul class="features-list">
                        <li>✓ Up to 10 users</li>
                        <li>✓ Basic features</li>
                        <li>✓ Email support</li>
                        <li>✓ 5GB storage</li>
                    </ul>
                    <button class="pricing-button" data-cta>Get Started</button>
                </div>

                <div class="pricing-card featured">
                    <div class="badge">Most Popular</div>
                    <h3>Professional</h3>
                    <div class="price">$99<span>/month</span></div>
                    <ul class="features-list">
                        <li>✓ Up to 50 users</li>
                        <li>✓ All features</li>
                        <li>✓ Priority support</li>
                        <li>✓ 50GB storage</li>
                    </ul>
                    <button class="pricing-button primary" data-cta>Get Started</button>
                </div>

                <div class="pricing-card">
                    <h3>Enterprise</h3>
                    <div class="price">Custom</div>
                    <ul class="features-list">
                        <li>✓ Unlimited users</li>
                        <li>✓ Custom features</li>
                        <li>✓ Dedicated support</li>
                        <li>✓ Unlimited storage</li>
                    </ul>
                    <button class="pricing-button" data-cta>Contact Sales</button>
                </div>
            </div>
        </div>
    </section>

    <section id="faq" class="faq">
        <div class="container">
            <h2>Frequently Asked Questions</h2>
            <div class="faq-list">
                <div class="faq-item">
                    <h3>How does the free trial work?</h3>
                    <p>Get full access to all features for 14 days. No credit card required.</p>
                </div>
                <div class="faq-item">
                    <h3>Can I upgrade or downgrade?</h3>
                    <p>Yes! Change your plan anytime. Changes take effect immediately.</p>
                </div>
                <div class="faq-item">
                    <h3>What payment methods do you accept?</h3>
                    <p>We accept all major credit cards, PayPal, and wire transfers.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="final-cta">
        <div class="container">
            <h2>Ready to transform your {{industry}} business, {{lead_name}}?</h2>
            <p>Join thousands of companies already using our platform</p>
            <button class="cta-large" data-cta>{{cta_text}}</button>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {{company_name}}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

SAAS_CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: {{font_family}};
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.navbar {
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: fixed;
    width: 100%;
    z-index: 1000;
    padding: 1rem 0;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: {{primary_color}};
}

.nav-menu {
    display: flex;
    align-items: center;
    gap: 2rem;
}

.nav-menu a {
    color: #333;
    text-decoration: none;
}

.nav-cta {
    background: {{primary_color}};
    color: white;
    border: none;
    padding: 0.5rem 1.5rem;
    border-radius: {{border_radius}};
    cursor: pointer;
}

.hero {
    padding: 8rem 0 4rem;
    margin-top: 60px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.hero .container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
}

.hero-content h1 {
    font-size: 3rem;
    color: {{primary_color}};
    margin-bottom: 1rem;
}

.hero-content p {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    color: #555;
}

.cta-primary {
    background: {{primary_color}};
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: {{border_radius}};
    cursor: pointer;
    transition: transform 0.2s;
}

.cta-primary:hover {
    transform: translateY(-2px);
}

.cta-note {
    margin-top: 1rem;
    font-size: 0.875rem;
    color: #777;
}

.mockup {
    background: white;
    padding: 4rem 2rem;
    border-radius: {{border_radius}};
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    text-align: center;
    font-size: 2rem;
}

.features {
    padding: 4rem 0;
}

.features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: {{primary_color}};
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}

.feature-box {
    text-align: center;
    padding: 2rem;
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature-box h3 {
    color: {{primary_color}};
    margin-bottom: 1rem;
}

.pricing {
    background: #f8f9fa;
    padding: 4rem 0;
}

.pricing h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: {{primary_color}};
}

.pricing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.pricing-card {
    background: white;
    padding: 2rem;
    border-radius: {{border_radius}};
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    position: relative;
}

.pricing-card.featured {
    transform: scale(1.05);
    border: 2px solid {{primary_color}};
}

.badge {
    background: {{accent_color}};
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    position: absolute;
    top: -15px;
    right: 20px;
    font-size: 0.875rem;
}

.pricing-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: {{primary_color}};
}

.price {
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 2rem;
    color: {{primary_color}};
}

.price span {
    font-size: 1rem;
    color: #777;
}

.features-list {
    list-style: none;
    margin-bottom: 2rem;
}

.features-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
}

.pricing-button {
    width: 100%;
    padding: 1rem;
    border: 2px solid {{primary_color}};
    background: white;
    color: {{primary_color}};
    border-radius: {{border_radius}};
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.3s;
}

.pricing-button.primary {
    background: {{primary_color}};
    color: white;
}

.pricing-button:hover {
    transform: translateY(-2px);
}

.faq {
    padding: 4rem 0;
}

.faq h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: {{primary_color}};
}

.faq-list {
    max-width: 800px;
    margin: 0 auto;
}

.faq-item {
    background: white;
    padding: 2rem;
    margin-bottom: 1rem;
    border-radius: {{border_radius}};
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.faq-item h3 {
    color: {{primary_color}};
    margin-bottom: 0.5rem;
}

.final-cta {
    background: {{primary_color}};
    color: white;
    padding: 4rem 0;
    text-align: center;
}

.final-cta h2 {
    color: white;
    margin-bottom: 1rem;
}

.cta-large {
    background: white;
    color: {{primary_color}};
    border: none;
    padding: 1.5rem 3rem;
    font-size: 1.25rem;
    border-radius: {{border_radius}};
    cursor: pointer;
    margin-top: 2rem;
    transition: transform 0.2s;
}

.cta-large:hover {
    transform: scale(1.05);
}

.footer {
    background: #333;
    color: white;
    padding: 2rem 0;
    text-align: center;
}

@media (max-width: 768px) {
    .hero .container {
        grid-template-columns: 1fr;
    }

    .hero-content h1 {
        font-size: 2rem;
    }

    .nav-menu {
        display: none;
    }

    .pricing-card.featured {
        transform: none;
    }
}
"""


async def seed_templates():
    """Seed demo site templates into database."""
    print("Seeding demo site templates...")

    async with async_session() as session:
        # Check if templates already exist
        from sqlalchemy import select
        result = await session.execute(select(DemoSiteTemplate))
        existing = result.scalars().all()

        if len(existing) > 0:
            print(f"Found {len(existing)} existing templates. Skipping seed.")
            return

        # Create Landing Page Template
        landing_template = DemoSiteTemplate(
            template_name="Modern Landing Page",
            template_type="landing",
            description="Professional landing page template with hero, features, testimonials, and CTA sections. Perfect for service businesses.",
            html_template=LANDING_PAGE_HTML.strip(),
            css_template=LANDING_PAGE_CSS.strip(),
            js_template="",
            customization_options={
                "colors": ["primary_color", "secondary_color", "accent_color"],
                "fonts": ["font_family"],
                "sections": ["hero", "features", "testimonials", "cta"],
                "required_fields": ["headline", "subheadline", "cta_text", "company_name"]
            },
            default_meta_title="{{company_name}} - {{headline}}",
            default_meta_description="{{subheadline}}",
            default_meta_keywords="landing page, business, {{industry}}",
            is_active=True,
            is_default=True
        )

        # Create Portfolio Template
        portfolio_template = DemoSiteTemplate(
            template_name="Professional Portfolio",
            template_type="portfolio",
            description="Clean portfolio template showcasing projects, skills, and contact information. Ideal for freelancers and agencies.",
            html_template=PORTFOLIO_HTML.strip(),
            css_template=PORTFOLIO_CSS.strip(),
            js_template="",
            customization_options={
                "colors": ["primary_color", "secondary_color", "accent_color"],
                "fonts": ["font_family"],
                "sections": ["about", "projects", "skills", "contact"],
                "required_fields": ["lead_name", "tagline", "about_text"]
            },
            default_meta_title="{{lead_name}} - Professional Portfolio",
            default_meta_description="{{about_text}}",
            default_meta_keywords="portfolio, projects, {{industry}}",
            is_active=True,
            is_default=False
        )

        # Create SaaS Demo Template
        saas_template = DemoSiteTemplate(
            template_name="SaaS Product Demo",
            template_type="saas",
            description="Complete SaaS product page with features, pricing tiers, FAQ, and conversion-focused design. Great for software products.",
            html_template=SAAS_HTML.strip(),
            css_template=SAAS_CSS.strip(),
            js_template="",
            customization_options={
                "colors": ["primary_color", "secondary_color", "accent_color"],
                "fonts": ["font_family"],
                "sections": ["hero", "features", "pricing", "faq", "final_cta"],
                "required_fields": ["headline", "subheadline", "cta_text", "company_name", "lead_name"]
            },
            default_meta_title="{{company_name}} - {{headline}}",
            default_meta_description="{{subheadline}}",
            default_meta_keywords="saas, software, {{industry}}, pricing",
            is_active=True,
            is_default=False
        )

        # Add all templates
        session.add(landing_template)
        session.add(portfolio_template)
        session.add(saas_template)

        await session.commit()

        print("✓ Successfully seeded 3 demo site templates:")
        print("  1. Modern Landing Page (default)")
        print("  2. Professional Portfolio")
        print("  3. SaaS Product Demo")


if __name__ == "__main__":
    asyncio.run(seed_templates())
