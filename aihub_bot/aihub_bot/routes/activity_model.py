"""
Activity model for FastAPI request validation.

The Microsoft 365 Agents SDK uses Pydantic models natively,
so we can directly use the Activity class without conversion.
"""

from microsoft_agents.activity import Activity

# Export Activity as ActivityModel for backward compatibility
ActivityModel = Activity
