"""Test API routes registration."""
from app.main import app

print("✅ FastAPI app imported successfully")

routes = [r.path for r in app.routes if hasattr(r, 'path')]
ai_routes = [r for r in routes if 'ai-mvp' in r]

print(f"✅ Total routes: {len(routes)}")
print(f"✅ AI MVP routes registered: {len(ai_routes)}")

for route in ai_routes:
    print(f"   - {route}")
