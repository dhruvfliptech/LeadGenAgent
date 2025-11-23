"""
Demo Site Builder - Generate improved website code from improvement plans.

Uses AI Council to generate production-ready code in multiple frameworks:
- Plain HTML/CSS/JS for simple sites
- React for interactive SPAs
- Next.js for full-stack applications

Architecture:
1. Takes improvement plan + original site
2. Uses AI to generate complete codebase
3. Validates syntax and structure
4. Returns deployable code with instructions
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from pydantic import BaseModel, Field
import structlog

from app.services.ai_mvp.ai_council import AICouncil, Message, AICouncilResponse
from app.services.ai_mvp.semantic_router import TaskType

logger = structlog.get_logger(__name__)


class Framework(str, Enum):
    """Supported frameworks for demo site generation."""
    HTML = "html"
    REACT = "react"
    NEXTJS = "nextjs"


class BuildStatus(str, Enum):
    """Build status for demo sites."""
    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class FileDefinition(BaseModel):
    """Definition of a generated file."""
    path: str = Field(..., description="File path relative to project root")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language (html, css, js, tsx, json, md)")
    purpose: str = Field(..., description="Purpose of this file")


class DeploymentConfig(BaseModel):
    """Deployment configuration for the demo site."""
    framework: Framework
    build_command: str = Field(..., description="Command to build the site")
    install_command: str = Field(..., description="Command to install dependencies")
    output_directory: str = Field(..., description="Build output directory")
    dev_command: str = Field(..., description="Command to run dev server")
    port: int = Field(default=3000, description="Default dev server port")
    environment_variables: Dict[str, str] = Field(default_factory=dict)


class DemoSiteBuild(BaseModel):
    """Complete demo site build result."""
    framework: Framework
    files: Dict[str, str] = Field(..., description="Map of file paths to content")
    deployment_config: DeploymentConfig
    preview_url: Optional[str] = Field(None, description="URL after deployment")
    status: BuildStatus = Field(default=BuildStatus.PENDING)

    # Metadata
    improvements_applied: List[str] = Field(default_factory=list)
    generation_time_seconds: float = 0.0
    total_lines_of_code: int = 0
    ai_model_used: str = ""
    ai_cost: float = 0.0
    validation_results: Dict[str, Any] = Field(default_factory=dict)


class ImprovementPlan(BaseModel):
    """Improvement plan from Phase 3 analysis."""
    overall_strategy: str
    improvements: List[Dict[str, Any]]
    priority_order: List[str]
    estimated_impact: str


class OriginalSite(BaseModel):
    """Original website data."""
    url: str
    html_content: str
    title: str
    meta_description: Optional[str] = None
    styles: Optional[str] = None
    scripts: Optional[str] = None


class DemoSiteBuilder:
    """
    Generate complete demo sites with improvements applied.

    Features:
    - Multi-framework support (HTML, React, Next.js)
    - AI-powered code generation
    - Automatic file structure creation
    - Syntax validation
    - Deployment configuration
    - Inline improvement comments
    """

    def __init__(self, ai_council: AICouncil):
        """
        Initialize demo site builder.

        Args:
            ai_council: AI Council for code generation
        """
        self.ai_council = ai_council

    async def build_demo_site(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        framework: Framework = Framework.REACT,
        lead_value: Optional[float] = None,
        include_comments: bool = True
    ) -> DemoSiteBuild:
        """
        Build a complete demo site with improvements applied.

        Args:
            original_site: Original website data
            improvement_plan: Improvement plan from analysis
            framework: Target framework (html, react, nextjs)
            lead_value: Lead value for AI routing
            include_comments: Include explanation comments in code

        Returns:
            Complete demo site build with all files
        """
        import time
        start_time = time.time()

        logger.info(
            "demo_builder.starting",
            url=original_site.url,
            framework=framework.value,
            improvements_count=len(improvement_plan.improvements)
        )

        try:
            # Step 1: Generate file structure plan
            file_structure = await self._plan_file_structure(
                framework=framework,
                improvement_plan=improvement_plan
            )

            # Step 2: Generate each file with AI
            files = await self._generate_all_files(
                original_site=original_site,
                improvement_plan=improvement_plan,
                framework=framework,
                file_structure=file_structure,
                lead_value=lead_value,
                include_comments=include_comments
            )

            # Step 3: Validate generated code
            validation_results = await self._validate_code(files, framework)

            # Step 4: Create deployment config
            deployment_config = self._create_deployment_config(framework)

            # Step 5: Calculate metadata
            total_lines = sum(len(content.split('\n')) for content in files.values())
            generation_time = time.time() - start_time

            # Step 6: Extract improvements applied
            improvements_applied = [
                imp.get('title', imp.get('category', 'Unknown'))
                for imp in improvement_plan.improvements
            ]

            build = DemoSiteBuild(
                framework=framework,
                files=files,
                deployment_config=deployment_config,
                status=BuildStatus.COMPLETED,
                improvements_applied=improvements_applied,
                generation_time_seconds=generation_time,
                total_lines_of_code=total_lines,
                validation_results=validation_results
            )

            logger.info(
                "demo_builder.completed",
                framework=framework.value,
                files_count=len(files),
                lines_of_code=total_lines,
                generation_time=generation_time
            )

            return build

        except Exception as e:
            logger.error(
                "demo_builder.failed",
                url=original_site.url,
                framework=framework.value,
                error=str(e)
            )
            raise

    async def _plan_file_structure(
        self,
        framework: Framework,
        improvement_plan: ImprovementPlan
    ) -> Dict[str, str]:
        """
        Plan the file structure for the demo site.

        Args:
            framework: Target framework
            improvement_plan: Improvement plan

        Returns:
            Dict mapping file paths to their purposes
        """
        if framework == Framework.HTML:
            return {
                "index.html": "Main HTML page with improvements",
                "styles.css": "Improved CSS styles",
                "script.js": "Enhanced JavaScript functionality",
                "README.md": "Documentation and improvements list"
            }

        elif framework == Framework.REACT:
            return {
                "package.json": "NPM dependencies and scripts",
                "src/App.tsx": "Main React application component",
                "src/components/Hero.tsx": "Improved hero section",
                "src/components/Features.tsx": "Enhanced features section",
                "src/components/CTA.tsx": "Optimized call-to-action",
                "src/styles/globals.css": "Global styles with improvements",
                "src/hooks/useForm.ts": "Form handling hook (if needed)",
                "public/index.html": "HTML template",
                "README.md": "Setup and improvements documentation",
                "tsconfig.json": "TypeScript configuration",
                ".gitignore": "Git ignore file"
            }

        elif framework == Framework.NEXTJS:
            return {
                "package.json": "NPM dependencies and scripts",
                "app/page.tsx": "Main page component",
                "app/layout.tsx": "Root layout with metadata",
                "app/globals.css": "Global styles",
                "components/Hero.tsx": "Hero section component",
                "components/Features.tsx": "Features section component",
                "components/CTA.tsx": "Call-to-action component",
                "lib/analytics.ts": "Analytics integration",
                "public/robots.txt": "SEO robots file",
                "next.config.js": "Next.js configuration",
                "README.md": "Setup and improvements documentation",
                "tsconfig.json": "TypeScript configuration",
                ".gitignore": "Git ignore file"
            }

        return {}

    async def _generate_all_files(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        framework: Framework,
        file_structure: Dict[str, str],
        lead_value: Optional[float],
        include_comments: bool
    ) -> Dict[str, str]:
        """
        Generate all files for the demo site.

        Args:
            original_site: Original site data
            improvement_plan: Improvement plan
            framework: Target framework
            file_structure: Planned file structure
            lead_value: Lead value for routing
            include_comments: Include explanation comments

        Returns:
            Dict mapping file paths to content
        """
        files = {}

        # Generate core files with AI
        if framework == Framework.HTML:
            files = await self._generate_html_site(
                original_site, improvement_plan, lead_value, include_comments
            )
        elif framework == Framework.REACT:
            files = await self._generate_react_site(
                original_site, improvement_plan, lead_value, include_comments
            )
        elif framework == Framework.NEXTJS:
            files = await self._generate_nextjs_site(
                original_site, improvement_plan, lead_value, include_comments
            )

        return files

    async def _generate_html_site(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        lead_value: Optional[float],
        include_comments: bool
    ) -> Dict[str, str]:
        """Generate plain HTML/CSS/JS site."""

        # Build comprehensive prompt
        prompt = self._build_html_generation_prompt(
            original_site, improvement_plan, include_comments
        )

        # Call AI to generate code
        response = await self.ai_council.complete(
            task_type=TaskType.DEMO_SITE_PLANNING,  # Complex task
            messages=[
                Message(role="system", content=self._get_system_prompt("html")),
                Message(role="user", content=prompt)
            ],
            lead_value=lead_value,
            temperature=0.3,  # Lower temp for more consistent code
            max_tokens=4000
        )

        # Parse AI response into files
        files = self._parse_ai_code_response(response.content, Framework.HTML)

        # Add README if not present
        if "README.md" not in files:
            files["README.md"] = self._generate_readme(
                Framework.HTML, improvement_plan, original_site.url
            )

        return files

    async def _generate_react_site(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        lead_value: Optional[float],
        include_comments: bool
    ) -> Dict[str, str]:
        """Generate React site with TypeScript."""

        prompt = self._build_react_generation_prompt(
            original_site, improvement_plan, include_comments
        )

        response = await self.ai_council.complete(
            task_type=TaskType.DEMO_SITE_PLANNING,
            messages=[
                Message(role="system", content=self._get_system_prompt("react")),
                Message(role="user", content=prompt)
            ],
            lead_value=lead_value,
            temperature=0.3,
            max_tokens=6000
        )

        files = self._parse_ai_code_response(response.content, Framework.REACT)

        # Add configuration files
        files.update(self._get_react_config_files())

        # Add README
        if "README.md" not in files:
            files["README.md"] = self._generate_readme(
                Framework.REACT, improvement_plan, original_site.url
            )

        return files

    async def _generate_nextjs_site(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        lead_value: Optional[float],
        include_comments: bool
    ) -> Dict[str, str]:
        """Generate Next.js site with App Router."""

        prompt = self._build_nextjs_generation_prompt(
            original_site, improvement_plan, include_comments
        )

        response = await self.ai_council.complete(
            task_type=TaskType.DEMO_SITE_PLANNING,
            messages=[
                Message(role="system", content=self._get_system_prompt("nextjs")),
                Message(role="user", content=prompt)
            ],
            lead_value=lead_value,
            temperature=0.3,
            max_tokens=6000
        )

        files = self._parse_ai_code_response(response.content, Framework.NEXTJS)

        # Add configuration files
        files.update(self._get_nextjs_config_files())

        # Add README
        if "README.md" not in files:
            files["README.md"] = self._generate_readme(
                Framework.NEXTJS, improvement_plan, original_site.url
            )

        return files

    def _get_system_prompt(self, framework: str) -> str:
        """Get system prompt for code generation."""

        base_prompt = """You are an expert web developer and UI/UX designer. Generate production-ready code that:

1. **Applies all improvements** from the improvement plan
2. **Preserves original functionality** while enhancing it
3. **Includes inline comments** explaining each improvement
4. **Uses modern best practices** (accessibility, SEO, performance)
5. **Is visually impressive** with clean, modern design
6. **Is fully functional** - no placeholder code

Code quality standards:
- Clean, readable, well-commented code
- Semantic HTML5
- Mobile-responsive design
- Fast loading and performance optimized
- Accessibility (WCAG AA compliant)
- SEO optimized with proper meta tags
"""

        if framework == "html":
            return base_prompt + """
Output format: Provide the complete code for each file in this EXACT format:

```html
<!-- FILE: index.html -->
<!DOCTYPE html>
<html lang="en">
...full code...
</html>
```

```css
/* FILE: styles.css */
/* Improved styles with comments */
body { ... }
```

```javascript
// FILE: script.js
// Enhanced functionality
console.log('Demo site loaded');
```

Generate all files in this format."""

        elif framework == "react":
            return base_prompt + """
Tech stack: React 18 + TypeScript + Vite + CSS Modules

Output format: Provide complete code for each file:

```tsx
// FILE: src/App.tsx
import React from 'react';
...full code...
```

```json
// FILE: package.json
{
  "name": "demo-site",
  ...
}
```

Generate all files in this format. Use modern React patterns (hooks, functional components)."""

        elif framework == "nextjs":
            return base_prompt + """
Tech stack: Next.js 14 + App Router + TypeScript + Tailwind CSS

Output format: Provide complete code for each file:

```tsx
// FILE: app/page.tsx
export default function Page() {
  ...full code...
}
```

```typescript
// FILE: lib/analytics.ts
export function trackEvent() { ... }
```

Generate all files in this format. Use Next.js 14 App Router patterns."""

        return base_prompt

    def _build_html_generation_prompt(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        include_comments: bool
    ) -> str:
        """Build prompt for HTML generation."""

        improvements_text = "\n".join([
            f"{i+1}. **{imp.get('title', 'Improvement')}**: {imp.get('description', '')}"
            for i, imp in enumerate(improvement_plan.improvements[:10])
        ])

        return f"""Generate a complete HTML/CSS/JS website based on this original site and improvements.

**ORIGINAL SITE**:
URL: {original_site.url}
Title: {original_site.title}

HTML Preview (first 2000 chars):
{original_site.html_content[:2000]}

**IMPROVEMENT PLAN**:
Strategy: {improvement_plan.overall_strategy}

Key Improvements:
{improvements_text}

**YOUR TASK**:
Generate a complete, modern website with all improvements applied. Include:
- index.html (full HTML5 structure)
- styles.css (modern CSS with improvements)
- script.js (enhanced functionality)

Make it visually impressive and fully functional. {'Add inline comments explaining each improvement.' if include_comments else ''}"""

    def _build_react_generation_prompt(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        include_comments: bool
    ) -> str:
        """Build prompt for React generation."""

        improvements_text = "\n".join([
            f"{i+1}. **{imp.get('title', 'Improvement')}**: {imp.get('description', '')}"
            for i, imp in enumerate(improvement_plan.improvements[:10])
        ])

        return f"""Generate a complete React application based on this original site and improvements.

**ORIGINAL SITE**:
URL: {original_site.url}
Title: {original_site.title}
Description: {original_site.meta_description or 'N/A'}

**IMPROVEMENT PLAN**:
Strategy: {improvement_plan.overall_strategy}

Key Improvements:
{improvements_text}

**YOUR TASK**:
Generate a complete React app with TypeScript. Include:
- src/App.tsx (main component)
- src/components/Hero.tsx (hero section)
- src/components/Features.tsx (features section)
- src/components/CTA.tsx (call-to-action)
- src/styles/globals.css (modern styles)
- package.json (with all dependencies)

Use modern React patterns (hooks, functional components, TypeScript). Make it visually stunning and production-ready. {'Add comments explaining improvements.' if include_comments else ''}"""

    def _build_nextjs_generation_prompt(
        self,
        original_site: OriginalSite,
        improvement_plan: ImprovementPlan,
        include_comments: bool
    ) -> str:
        """Build prompt for Next.js generation."""

        improvements_text = "\n".join([
            f"{i+1}. **{imp.get('title', 'Improvement')}**: {imp.get('description', '')}"
            for i, imp in enumerate(improvement_plan.improvements[:10])
        ])

        return f"""Generate a complete Next.js 14 application with App Router based on this original site and improvements.

**ORIGINAL SITE**:
URL: {original_site.url}
Title: {original_site.title}
Description: {original_site.meta_description or 'N/A'}

**IMPROVEMENT PLAN**:
Strategy: {improvement_plan.overall_strategy}

Key Improvements:
{improvements_text}

**YOUR TASK**:
Generate a complete Next.js app with:
- app/page.tsx (main page with Server Components)
- app/layout.tsx (root layout with metadata)
- app/globals.css (Tailwind + custom styles)
- components/Hero.tsx (hero section)
- components/Features.tsx (features section)
- components/CTA.tsx (call-to-action)
- lib/analytics.ts (analytics helper)
- package.json (with Next.js 14 dependencies)

Use Next.js 14 best practices (App Router, Server Components, metadata API). Make it production-ready and visually impressive. {'Add comments explaining improvements.' if include_comments else ''}"""

    def _parse_ai_code_response(
        self,
        response: str,
        framework: Framework
    ) -> Dict[str, str]:
        """
        Parse AI response into file paths and content.

        Args:
            response: AI generated code response
            framework: Target framework

        Returns:
            Dict mapping file paths to content
        """
        files = {}

        # Pattern to match code blocks with file paths
        # Matches: ```language\n// FILE: path/to/file.ext\n...code...```
        # Also handles: <!-- FILE: path -->
        pattern = r'```(?:\w+)?\s*\n?(?://|/\*|<!--)\s*FILE:\s*([^\n\->]+?)(?:\s*-->|\s*\*/|\s*)\n(.*?)```'

        matches = re.finditer(pattern, response, re.DOTALL | re.IGNORECASE)

        for match in matches:
            file_path = match.group(1).strip()
            content = match.group(2).strip()

            # Clean up file path - remove any trailing comment markers
            file_path = file_path.replace('\\', '/').replace('-->', '').strip()

            files[file_path] = content

            logger.info("demo_builder.parsed_file", path=file_path, size=len(content))

        # If no files were parsed, try to extract code blocks without FILE comments
        if not files:
            logger.warning("demo_builder.no_files_parsed", attempting_fallback=True)
            files = self._fallback_parse_code_blocks(response, framework)

        return files

    def _fallback_parse_code_blocks(
        self,
        response: str,
        framework: Framework
    ) -> Dict[str, str]:
        """
        Fallback parser when FILE comments aren't found.

        Args:
            response: AI response
            framework: Target framework

        Returns:
            Dict mapping inferred file paths to content
        """
        files = {}

        # Pattern to match any code blocks
        pattern = r'```(\w+)?\s*\n(.*?)```'
        matches = re.finditer(pattern, response, re.DOTALL)

        file_counter = {"html": 0, "css": 0, "js": 0, "tsx": 0, "json": 0, "ts": 0}

        for match in matches:
            language = match.group(1) or "txt"
            content = match.group(2).strip()

            # Infer file path based on language and framework
            if language == "html":
                file_path = "index.html" if file_counter["html"] == 0 else f"page{file_counter['html']}.html"
                file_counter["html"] += 1
            elif language == "css":
                file_path = "styles.css" if file_counter["css"] == 0 else f"styles{file_counter['css']}.css"
                file_counter["css"] += 1
            elif language == "javascript" or language == "js":
                file_path = "script.js" if file_counter["js"] == 0 else f"script{file_counter['js']}.js"
                file_counter["js"] += 1
            elif language == "tsx":
                file_path = f"src/Component{file_counter['tsx']}.tsx"
                file_counter["tsx"] += 1
            elif language == "json":
                file_path = "package.json" if file_counter["json"] == 0 else f"config{file_counter['json']}.json"
                file_counter["json"] += 1
            else:
                continue

            files[file_path] = content

        return files

    def _get_react_config_files(self) -> Dict[str, str]:
        """Get React configuration files."""

        package_json = """{
  "name": "demo-site",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}"""

        tsconfig = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}"""

        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})"""

        gitignore = """node_modules
dist
.DS_Store
*.log
.env.local"""

        return {
            "package.json": package_json,
            "tsconfig.json": tsconfig,
            "vite.config.ts": vite_config,
            ".gitignore": gitignore
        }

    def _get_nextjs_config_files(self) -> Dict[str, str]:
        """Get Next.js configuration files."""

        package_json = """{
  "name": "demo-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0"
  }
}"""

        next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
}

module.exports = nextConfig"""

        tsconfig = """{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""

        tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""

        gitignore = """node_modules
.next
.DS_Store
*.log
.env.local"""

        return {
            "package.json": package_json,
            "next.config.js": next_config,
            "tsconfig.json": tsconfig,
            "tailwind.config.js": tailwind_config,
            ".gitignore": gitignore
        }

    def _generate_readme(
        self,
        framework: Framework,
        improvement_plan: ImprovementPlan,
        original_url: str
    ) -> str:
        """Generate README.md with setup instructions and improvements list."""

        if framework == Framework.HTML:
            setup = """## Setup

1. Open `index.html` in a web browser
2. No build process required - it's plain HTML/CSS/JS"""

        elif framework == Framework.REACT:
            setup = """## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```"""

        elif framework == Framework.NEXTJS:
            setup = """## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000

3. Build for production:
   ```bash
   npm run build
   npm start
   ```"""

        improvements_list = "\n".join([
            f"{i+1}. **{imp.get('title', 'Improvement')}**: {imp.get('description', '')}"
            for i, imp in enumerate(improvement_plan.improvements)
        ])

        return f"""# Demo Site - Improved Version

Generated from: {original_url}

## Overview

{improvement_plan.overall_strategy}

{setup}

## Improvements Applied

{improvements_list}

## Technology Stack

Framework: **{framework.value.upper()}**

## Deployment

This site is ready to deploy to:
- Vercel (recommended for Next.js/React)
- Netlify
- GitHub Pages (for HTML)
- Any static hosting service

## Notes

- All improvements have been applied with inline comments
- Code follows modern best practices
- Fully responsive and accessible
- SEO optimized

Generated with AI-powered demo builder.
"""

    async def _validate_code(
        self,
        files: Dict[str, str],
        framework: Framework
    ) -> Dict[str, Any]:
        """
        Validate generated code for syntax errors.

        Args:
            files: Generated files
            framework: Target framework

        Returns:
            Validation results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "file_count": len(files),
            "total_size_bytes": sum(len(content.encode('utf-8')) for content in files.values())
        }

        # Basic validation checks
        for file_path, content in files.items():
            # Check if file is empty
            if not content.strip():
                results["errors"].append(f"{file_path}: File is empty")
                results["is_valid"] = False

            # Check for common syntax issues
            if file_path.endswith('.json'):
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    results["errors"].append(f"{file_path}: Invalid JSON - {str(e)}")
                    results["is_valid"] = False

            # Check for placeholder comments
            placeholders = [
                "TODO", "FIXME", "PLACEHOLDER", "...", "your code here",
                "implement this", "add your"
            ]
            for placeholder in placeholders:
                if placeholder.lower() in content.lower():
                    results["warnings"].append(
                        f"{file_path}: Contains placeholder '{placeholder}'"
                    )

        # Framework-specific checks
        if framework == Framework.HTML:
            if "index.html" not in files:
                results["errors"].append("Missing index.html")
                results["is_valid"] = False

        elif framework in [Framework.REACT, Framework.NEXTJS]:
            if "package.json" not in files:
                results["errors"].append("Missing package.json")
                results["is_valid"] = False

        logger.info(
            "demo_builder.validation_complete",
            is_valid=results["is_valid"],
            errors_count=len(results["errors"]),
            warnings_count=len(results["warnings"])
        )

        return results

    def _create_deployment_config(self, framework: Framework) -> DeploymentConfig:
        """Create deployment configuration for the framework."""

        if framework == Framework.HTML:
            return DeploymentConfig(
                framework=framework,
                build_command="# No build needed",
                install_command="# No install needed",
                output_directory=".",
                dev_command="python -m http.server 8000",
                port=8000
            )

        elif framework == Framework.REACT:
            return DeploymentConfig(
                framework=framework,
                build_command="npm run build",
                install_command="npm install",
                output_directory="dist",
                dev_command="npm run dev",
                port=5173
            )

        elif framework == Framework.NEXTJS:
            return DeploymentConfig(
                framework=framework,
                build_command="npm run build",
                install_command="npm install",
                output_directory=".next",
                dev_command="npm run dev",
                port=3000,
                environment_variables={
                    "NODE_ENV": "production"
                }
            )

        return DeploymentConfig(
            framework=framework,
            build_command="",
            install_command="",
            output_directory="",
            dev_command=""
        )


# Utility function for quick demo generation
async def build_demo_quick(
    url: str,
    html_content: str,
    improvement_plan_dict: Dict[str, Any],
    ai_council: AICouncil,
    framework: Framework = Framework.REACT
) -> DemoSiteBuild:
    """
    Quick demo site generation.

    Args:
        url: Original site URL
        html_content: Original HTML
        improvement_plan_dict: Improvement plan as dict
        ai_council: AI Council instance
        framework: Target framework

    Returns:
        Complete demo site build
    """
    builder = DemoSiteBuilder(ai_council)

    original_site = OriginalSite(
        url=url,
        html_content=html_content,
        title="Demo Site"
    )

    improvement_plan = ImprovementPlan(**improvement_plan_dict)

    return await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=framework
    )
