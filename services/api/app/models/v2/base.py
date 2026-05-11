"""Base model for SQLAlchemy declarative classes.

Uses the same Base as v1 models to ensure all tables are created together.
"""

# Re-export from v1 base to keep imports consistent
from app.models.base import Base