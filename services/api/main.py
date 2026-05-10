"""
feltabout API entry point.

This file redirects to the new modular structure in app/.
For local development, run: uvicorn main:app --reload
"""

from app.main import app

__all__ = ["app"]