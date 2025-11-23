"""
API Integration Example for Demo Site Builder

Shows how to integrate the demo builder into FastAPI endpoints for Phase 3.
This is an example - actual implementation would go in app/api/endpoints/phase3.py
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.demo_builder import (
    DemoSiteBuilder,
    Framework,
    ImprovementPlan,
    OriginalSite,
    DemoSiteBuild,
    BuildStatus
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker
from app.core.config import settings


# API Request/Response Models

class DemoSiteRequest(BaseModel):
    """Request to generate a demo site."""
    lead_id: int = Field(..., description="Lead ID for tracking")
    original_url: str = Field(..., description="Original website URL")
    original_html: str = Field(..., description="Original HTML content")
    improvement_plan: Dict[str, Any] = Field(..., description="Improvement plan from analysis")
    framework: Framework = Field(default=Framework.REACT, description="Target framework")
    include_comments: bool = Field(default=True, description="Include explanation comments")


class DemoSiteResponse(BaseModel):
    """Response with generated demo site."""
    build_id: str
    status: BuildStatus
    framework: str
    files: Dict[str, str]
    deployment_config: Dict[str, Any]
    improvements_applied: List[str]
    generation_time_seconds: float
    total_lines_of_code: int
    ai_model_used: str
    ai_cost: float
    validation_results: Dict[str, Any]
    preview_url: Optional[str] = None


class DemoSiteBuildStatus(BaseModel):
    """Status of a demo site build."""
    build_id: str
    status: BuildStatus
    progress_percentage: int
    current_step: str
    error_message: Optional[str] = None


# API Router (would go in app/api/endpoints/phase3.py)

router = APIRouter(prefix="/api/v1/phase3", tags=["Phase 3 - Demo Builder"])


# Dependency injection

async def get_ai_council() -> AICouncil:
    """Get AI Council instance."""
    config = AICouncilConfig(
        openrouter_api_key=settings.OPENAI_API_KEY,  # Or OPENROUTER_API_KEY
        default_temperature=0.3,
        default_max_tokens=6000
    )
    gym_tracker = AIGymTracker()  # Optional: for cost tracking
    ai_council = AICouncil(config, gym_tracker=gym_tracker)
    try:
        yield ai_council
    finally:
        await ai_council.close()


# API Endpoints

@router.post("/demo-sites", response_model=DemoSiteResponse, status_code=201)
async def generate_demo_site(
    request: DemoSiteRequest,
    background_tasks: BackgroundTasks,
    ai_council: AICouncil = Depends(get_ai_council)
):
    """
    Generate a demo site with improvements applied.

    This endpoint:
    1. Validates the request
    2. Generates the demo site using AI
    3. Returns the complete codebase
    4. Optionally deploys to preview environment (background task)

    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/phase3/demo-sites \\
      -H "Content-Type: application/json" \\
      -d '{
        "lead_id": 123,
        "original_url": "https://example.com",
        "original_html": "<html>...</html>",
        "improvement_plan": {...},
        "framework": "react",
        "include_comments": true
      }'
    ```
    """
    try:
        # Initialize builder
        builder = DemoSiteBuilder(ai_council)

        # Parse inputs
        original_site = OriginalSite(
            url=request.original_url,
            html_content=request.original_html,
            title="Demo Site"  # Could extract from HTML
        )

        improvement_plan = ImprovementPlan(**request.improvement_plan)

        # Get lead value for AI routing (optional)
        lead_value = None  # Could fetch from database based on lead_id

        # Generate demo site
        build = await builder.build_demo_site(
            original_site=original_site,
            improvement_plan=improvement_plan,
            framework=request.framework,
            lead_value=lead_value,
            include_comments=request.include_comments
        )

        # Generate build ID
        import uuid
        build_id = str(uuid.uuid4())

        # Background task: Save to database
        # background_tasks.add_task(save_demo_site_to_db, build_id, request.lead_id, build)

        # Background task: Deploy to preview environment
        # if deploy_enabled:
        #     background_tasks.add_task(deploy_to_vercel, build_id, build)

        # Return response
        return DemoSiteResponse(
            build_id=build_id,
            status=build.status,
            framework=build.framework.value,
            files=build.files,
            deployment_config={
                "framework": build.deployment_config.framework.value,
                "build_command": build.deployment_config.build_command,
                "install_command": build.deployment_config.install_command,
                "output_directory": build.deployment_config.output_directory,
                "dev_command": build.deployment_config.dev_command,
                "port": build.deployment_config.port
            },
            improvements_applied=build.improvements_applied,
            generation_time_seconds=build.generation_time_seconds,
            total_lines_of_code=build.total_lines_of_code,
            ai_model_used=build.ai_model_used or "unknown",
            ai_cost=build.ai_cost,
            validation_results=build.validation_results,
            preview_url=build.preview_url
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate demo site: {str(e)}"
        )


@router.get("/demo-sites/{build_id}", response_model=DemoSiteResponse)
async def get_demo_site(build_id: str):
    """
    Get a previously generated demo site.

    Retrieves the demo site from storage (database or S3).

    Example:
    ```bash
    curl http://localhost:8000/api/v1/phase3/demo-sites/abc123
    ```
    """
    # TODO: Fetch from database
    raise HTTPException(status_code=501, detail="Not implemented - fetch from database")


@router.get("/demo-sites/{build_id}/status", response_model=DemoSiteBuildStatus)
async def get_demo_site_status(build_id: str):
    """
    Get the status of a demo site build.

    Useful for long-running builds to check progress.

    Example:
    ```bash
    curl http://localhost:8000/api/v1/phase3/demo-sites/abc123/status
    ```
    """
    # TODO: Fetch status from cache/database
    raise HTTPException(status_code=501, detail="Not implemented - fetch status")


@router.post("/demo-sites/{build_id}/deploy")
async def deploy_demo_site(build_id: str, background_tasks: BackgroundTasks):
    """
    Deploy a demo site to a preview environment.

    Deploys to Vercel, Netlify, or similar platform.

    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/phase3/demo-sites/abc123/deploy
    ```
    """
    # TODO: Trigger deployment
    raise HTTPException(status_code=501, detail="Not implemented - deployment")


@router.get("/demo-sites/{build_id}/download")
async def download_demo_site(build_id: str):
    """
    Download demo site as ZIP file.

    Returns a ZIP archive of all generated files.

    Example:
    ```bash
    curl http://localhost:8000/api/v1/phase3/demo-sites/abc123/download -o demo-site.zip
    ```
    """
    # TODO: Create ZIP and return
    raise HTTPException(status_code=501, detail="Not implemented - download")


@router.delete("/demo-sites/{build_id}")
async def delete_demo_site(build_id: str):
    """
    Delete a demo site.

    Removes from storage and undeploys from preview environment.

    Example:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/phase3/demo-sites/abc123
    ```
    """
    # TODO: Delete from storage
    raise HTTPException(status_code=501, detail="Not implemented - delete")


# Background Task Functions

async def save_demo_site_to_db(build_id: str, lead_id: int, build: DemoSiteBuild):
    """Save demo site to database for later retrieval."""
    # TODO: Implement database storage
    pass


async def deploy_to_vercel(build_id: str, build: DemoSiteBuild):
    """Deploy demo site to Vercel for live preview."""
    # TODO: Implement Vercel deployment
    # 1. Create temporary directory
    # 2. Write all files
    # 3. Run vercel CLI or API
    # 4. Update build.preview_url
    # 5. Store preview URL in database
    pass


async def deploy_to_netlify(build_id: str, build: DemoSiteBuild):
    """Deploy demo site to Netlify for live preview."""
    # TODO: Implement Netlify deployment
    pass


# Usage Example

"""
1. Client sends improvement plan + original site
2. API generates demo site with AI
3. API returns complete codebase
4. Client can:
   - Download as ZIP
   - View files in browser
   - Deploy to preview environment
   - Share preview URL with customer

Full workflow:
┌──────────────┐
│ Analyze Site │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Generate Plan    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Build Demo Site  │ ← This service
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Deploy Preview   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Share with Lead  │
└──────────────────┘
"""


# Database Models (would go in app/models/phase3.py)

"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Enum
from app.models.base import Base
import enum

class DemoSiteStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPLOYED = "deployed"

class DemoSite(Base):
    __tablename__ = "demo_sites"

    id = Column(Integer, primary_key=True)
    build_id = Column(String, unique=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))

    # Build details
    framework = Column(String)
    status = Column(Enum(DemoSiteStatus))
    files = Column(JSON)  # Store as JSON or S3 URLs
    deployment_config = Column(JSON)

    # Metadata
    improvements_applied = Column(JSON)
    generation_time_seconds = Column(Float)
    total_lines_of_code = Column(Integer)
    ai_model_used = Column(String)
    ai_cost = Column(Float)
    validation_results = Column(JSON)

    # Deployment
    preview_url = Column(String, nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
"""


# Frontend Integration Example (React)

"""
// src/pages/DemoBuilder.tsx

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateDemoSite, DemoSiteRequest } from '../api/phase3';

export default function DemoBuilder({ lead, improvementPlan }) {
  const [framework, setFramework] = useState('react');

  const { mutate, isLoading, data } = useMutation({
    mutationFn: (request: DemoSiteRequest) => generateDemoSite(request),
  });

  const handleGenerate = () => {
    mutate({
      lead_id: lead.id,
      original_url: lead.url,
      original_html: lead.html_content,
      improvement_plan: improvementPlan,
      framework,
      include_comments: true,
    });
  };

  return (
    <div className="demo-builder">
      <h2>Generate Demo Site</h2>

      <select value={framework} onChange={(e) => setFramework(e.target.value)}>
        <option value="html">HTML/CSS/JS</option>
        <option value="react">React</option>
        <option value="nextjs">Next.js</option>
      </select>

      <button onClick={handleGenerate} disabled={isLoading}>
        {isLoading ? 'Generating...' : 'Generate Demo Site'}
      </button>

      {data && (
        <div className="results">
          <h3>Demo Site Generated!</h3>
          <p>Status: {data.status}</p>
          <p>Files: {Object.keys(data.files).length}</p>
          <p>Lines of Code: {data.total_lines_of_code}</p>
          <p>Cost: ${data.ai_cost.toFixed(4)}</p>

          <div className="files">
            {Object.entries(data.files).map(([path, content]) => (
              <FileViewer key={path} path={path} content={content} />
            ))}
          </div>

          <div className="actions">
            <button onClick={() => downloadZip(data.build_id)}>
              Download ZIP
            </button>
            <button onClick={() => deployPreview(data.build_id)}>
              Deploy Preview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
"""
