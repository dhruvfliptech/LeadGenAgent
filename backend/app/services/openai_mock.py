"""
This file is deprecated. AI functionality is now handled gracefully in the actual services.

If you see this being imported, it means the code needs to be updated to use proper
AI integration with error handling.

To enable AI features:
1. Install the OpenAI library: pip install openai
2. Set your API key in .env: OPENAI_API_KEY=your-key-here
3. Restart the application

The application will work without AI, but AI-powered features will be disabled.
"""

import warnings

warnings.warn(
    "openai_mock.py is deprecated. AI features should handle missing libraries gracefully. "
    "Please update the code to check for openai availability using try/except imports.",
    DeprecationWarning,
    stacklevel=2
)