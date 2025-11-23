"""
Vercel Deployment Integration - Usage Examples

This file demonstrates how to use the Vercel deployment integration
to deploy demo sites for leads in the Craigslist Lead Generation System.
"""

import asyncio
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.integrations.vercel_deployer import VercelDeployer
from app.models.demo_sites import DemoSite, DeploymentHistory
from app.models.leads import Lead
from app.core.database import AsyncSessionLocal


# ============================================================================
# Example 1: Simple HTML Site Deployment
# ============================================================================

async def example_1_simple_html_deployment():
    """Deploy a simple HTML demo site."""

    print("Example 1: Simple HTML Deployment")
    print("=" * 60)

    # Initialize deployer
    deployer = VercelDeployer()

    # Prepare simple HTML files
    files = {
        "index.html": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo Site for Lead</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>Welcome to Your Demo Site</h1>
        <p>This is a professionally designed demo site for your business.</p>
        <div class="cta">
            <button onclick="alert('Contact us!')">Get Started</button>
        </div>
    </div>
</body>
</html>
""",
        "styles.css": """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    background: white;
    padding: 3rem;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    text-align: center;
    max-width: 600px;
}

h1 {
    color: #333;
    margin-bottom: 1rem;
    font-size: 2.5rem;
}

p {
    color: #666;
    font-size: 1.125rem;
    margin-bottom: 2rem;
}

button {
    background: #667eea;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: transform 0.2s;
}

button:hover {
    transform: translateY(-2px);
}
"""
    }

    # Deploy to Vercel
    result = await deployer.deploy_demo_site(
        files=files,
        framework="html",
        project_name="demo-html-simple",
        lead_id=1  # Example lead ID
    )

    # Check result
    if result.success:
        print(f"✓ Deployment successful!")
        print(f"  URL: {result.url}")
        print(f"  Build time: {result.build_time:.2f}s")
        print(f"  Deployment ID: {result.deployment_id}")
    else:
        print(f"✗ Deployment failed: {result.error_message}")

    return result


# ============================================================================
# Example 2: Next.js Application Deployment
# ============================================================================

async def example_2_nextjs_deployment():
    """Deploy a Next.js demo site."""

    print("\nExample 2: Next.js Deployment")
    print("=" * 60)

    deployer = VercelDeployer()

    # Next.js project files
    files = {
        "package.json": """{
  "name": "demo-nextjs-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  }
}""",
        "pages/index.js": """
export default function Home() {
  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Professional Demo Site</h1>
      <p style={styles.description}>
        Built with Next.js - Lightning fast and SEO optimized
      </p>
      <div style={styles.features}>
        <div style={styles.feature}>
          <h3>Fast</h3>
          <p>Optimized performance</p>
        </div>
        <div style={styles.feature}>
          <h3>SEO</h3>
          <p>Search engine ready</p>
        </div>
        <div style={styles.feature}>
          <h3>Modern</h3>
          <p>Latest technology</p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    padding: '2rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    textAlign: 'center',
  },
  title: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  description: {
    fontSize: '1.25rem',
    marginBottom: '3rem',
  },
  features: {
    display: 'flex',
    gap: '2rem',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  feature: {
    background: 'rgba(255,255,255,0.1)',
    padding: '2rem',
    borderRadius: '12px',
    minWidth: '200px',
  },
};
""",
        "pages/_app.js": """
export default function App({ Component, pageProps }) {
  return <Component {...pageProps} />;
}
""",
        ".gitignore": """
node_modules
.next
out
.env*.local
"""
    }

    # Deploy with environment variables
    result = await deployer.deploy_demo_site(
        files=files,
        framework="nextjs",
        project_name="demo-nextjs-pro",
        lead_id=2,
        env_vars={
            "NEXT_PUBLIC_API_URL": "https://api.example.com",
            "NODE_ENV": "production"
        }
    )

    if result.success:
        print(f"✓ Next.js deployment successful!")
        print(f"  Production URL: {result.url}")
        print(f"  Preview URL: {result.preview_url}")
        print(f"  Framework detected: {result.framework_detected}")
    else:
        print(f"✗ Deployment failed: {result.error_message}")

    return result


# ============================================================================
# Example 3: Deploy and Save to Database
# ============================================================================

async def example_3_deploy_and_save(lead_id: int):
    """Deploy a demo site and save to database."""

    print(f"\nExample 3: Deploy and Save to Database (Lead {lead_id})")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # 1. Get lead from database
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()

        if not lead:
            print(f"✗ Lead {lead_id} not found")
            return

        print(f"✓ Found lead: {lead.title}")

        # 2. Generate personalized content
        files = {
            "index.html": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo for {lead.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; }}
        .info {{ color: #666; margin: 1rem 0; }}
        .contact {{ background: #667eea; color: white; padding: 1rem; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{lead.title}</h1>
        <div class="info">
            <p>{lead.description or 'Professional demo site'}</p>
        </div>
        <div class="contact">
            <h3>Get in Touch</h3>
            <p>Email: {lead.email or 'contact@example.com'}</p>
        </div>
    </div>
</body>
</html>
"""
        }

        # 3. Deploy to Vercel
        deployer = VercelDeployer()

        result = await deployer.deploy_demo_site(
            files=files,
            framework="html",
            project_name=f"demo-lead-{lead_id}",
            lead_id=lead_id
        )

        # 4. Save to database
        if result.success:
            total_size = sum(len(content.encode('utf-8')) for content in files.values())

            demo_site = DemoSite(
                lead_id=lead_id,
                vercel_project_id=result.project_id,
                vercel_deployment_id=result.deployment_id,
                project_name=f"demo-lead-{lead_id}",
                framework="html",
                url=result.url,
                preview_url=result.preview_url,
                status=result.status,
                build_time=result.build_time,
                framework_detected=result.framework_detected,
                regions=result.regions,
                files_count=len(files),
                total_size_bytes=total_size,
                deployment_duration=result.build_time,
                ssl_enabled=True,
                is_active=True
            )

            db.add(demo_site)
            await db.commit()
            await db.refresh(demo_site)

            # Add deployment history
            history = DeploymentHistory(
                demo_site_id=demo_site.id,
                event_type="created",
                new_status="ready",
                event_data=result.metadata
            )
            db.add(history)
            await db.commit()

            print(f"✓ Deployment saved to database!")
            print(f"  Database ID: {demo_site.id}")
            print(f"  URL: {demo_site.url}")

            return demo_site
        else:
            print(f"✗ Deployment failed: {result.error_message}")
            return None


# ============================================================================
# Example 4: Cost Estimation
# ============================================================================

async def example_4_cost_estimation():
    """Estimate deployment costs."""

    print("\nExample 4: Cost Estimation")
    print("=" * 60)

    deployer = VercelDeployer()

    # Scenario 1: Small site with low traffic
    cost1 = deployer.estimate_cost(
        files_count=10,
        total_size_bytes=500_000,  # 500KB
        estimated_page_views=1_000,  # 1K views/month
        estimated_build_minutes=0.5
    )

    print("\nScenario 1: Small site, low traffic")
    print(f"  Files: 10, Size: 500KB, Views: 1K/month")
    print(f"  Bandwidth: {cost1['bandwidth_gb']:.2f} GB")
    print(f"  Build time: {cost1['build_minutes']:.1f} min")
    print(f"  Additional cost: ${cost1['total_estimated_cost']:.2f}")
    print(f"  Total (with base): ${cost1['total_estimated_cost'] + cost1['monthly_base_cost']:.2f}")

    # Scenario 2: Large site with high traffic
    cost2 = deployer.estimate_cost(
        files_count=100,
        total_size_bytes=10_000_000,  # 10MB
        estimated_page_views=100_000,  # 100K views/month
        estimated_build_minutes=5.0
    )

    print("\nScenario 2: Large site, high traffic")
    print(f"  Files: 100, Size: 10MB, Views: 100K/month")
    print(f"  Bandwidth: {cost2['bandwidth_gb']:.2f} GB")
    print(f"  Build time: {cost2['build_minutes']:.1f} min")
    print(f"  Additional cost: ${cost2['total_estimated_cost']:.2f}")
    print(f"  Total (with base): ${cost2['total_estimated_cost'] + cost2['monthly_base_cost']:.2f}")


# ============================================================================
# Example 5: Batch Deployments
# ============================================================================

async def example_5_batch_deployments(lead_ids: list):
    """Deploy demo sites for multiple leads."""

    print(f"\nExample 5: Batch Deployments for {len(lead_ids)} leads")
    print("=" * 60)

    deployer = VercelDeployer()
    results = []

    async with AsyncSessionLocal() as db:
        for lead_id in lead_ids:
            print(f"\nDeploying for lead {lead_id}...")

            # Get lead
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()

            if not lead:
                print(f"  ✗ Lead {lead_id} not found, skipping")
                continue

            # Simple template
            files = {
                "index.html": f"<html><body><h1>Demo for {lead.title}</h1></body></html>"
            }

            # Deploy
            deploy_result = await deployer.deploy_demo_site(
                files=files,
                framework="html",
                project_name=f"demo-lead-{lead_id}",
                lead_id=lead_id
            )

            if deploy_result.success:
                print(f"  ✓ Success: {deploy_result.url}")
                results.append((lead_id, deploy_result.url))
            else:
                print(f"  ✗ Failed: {deploy_result.error_message}")

            # Rate limiting - wait a bit between deployments
            await asyncio.sleep(1)

    print(f"\n{'='*60}")
    print(f"Batch deployment complete: {len(results)}/{len(lead_ids)} successful")

    for lead_id, url in results:
        print(f"  Lead {lead_id}: {url}")

    return results


# ============================================================================
# Example 6: Get Deployment Status
# ============================================================================

async def example_6_get_status(deployment_id: str):
    """Check the status of a deployment."""

    print(f"\nExample 6: Get Deployment Status")
    print("=" * 60)

    deployer = VercelDeployer()

    success, data, error = await deployer.get_deployment_status(deployment_id)

    if success:
        print(f"✓ Deployment found!")
        print(f"  ID: {data.get('id')}")
        print(f"  Status: {data.get('readyState')}")
        print(f"  URL: {data.get('url')}")
        print(f"  Created: {data.get('createdAt')}")

        if data.get('readyState') == 'READY':
            print(f"  🎉 Deployment is live!")
        elif data.get('readyState') == 'BUILDING':
            print(f"  ⏳ Deployment is still building...")
        elif data.get('readyState') == 'ERROR':
            print(f"  ❌ Deployment failed!")
            print(f"  Error: {data.get('error', {}).get('message')}")
    else:
        print(f"✗ Failed to get status: {error}")


# ============================================================================
# Example 7: Analytics Query
# ============================================================================

async def example_7_analytics():
    """Query deployment analytics from database."""

    print("\nExample 7: Deployment Analytics")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # Total deployments
        result = await db.execute(
            select(DemoSite).where(DemoSite.is_deleted == False)
        )
        all_sites = result.scalars().all()

        print(f"\nTotal active deployments: {len(all_sites)}")

        # By status
        status_counts = {}
        for site in all_sites:
            status_counts[site.status] = status_counts.get(site.status, 0) + 1

        print("\nDeployments by status:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

        # By framework
        framework_counts = {}
        for site in all_sites:
            framework_counts[site.framework] = framework_counts.get(site.framework, 0) + 1

        print("\nDeployments by framework:")
        for framework, count in framework_counts.items():
            print(f"  {framework}: {count}")

        # Average build time
        build_times = [site.build_time for site in all_sites if site.build_time]
        if build_times:
            avg_build_time = sum(build_times) / len(build_times)
            print(f"\nAverage build time: {avg_build_time:.2f}s")
            print(f"Min: {min(build_times):.2f}s, Max: {max(build_times):.2f}s")


# ============================================================================
# Main execution
# ============================================================================

async def main():
    """Run all examples."""

    print("\n" + "="*60)
    print("VERCEL DEPLOYMENT INTEGRATION - EXAMPLES")
    print("="*60)

    # Example 1: Simple HTML
    # await example_1_simple_html_deployment()

    # Example 2: Next.js
    # await example_2_nextjs_deployment()

    # Example 3: Deploy and save (requires existing lead)
    # await example_3_deploy_and_save(lead_id=1)

    # Example 4: Cost estimation
    await example_4_cost_estimation()

    # Example 5: Batch deployments (requires existing leads)
    # await example_5_batch_deployments([1, 2, 3])

    # Example 6: Get status (requires deployment ID)
    # await example_6_get_status("dpl_xxx")

    # Example 7: Analytics
    # await example_7_analytics()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
