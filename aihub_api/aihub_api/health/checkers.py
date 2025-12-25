"""
Health check functions for verifying API dependencies.

These functions are used by the HealthController's readiness endpoint
to verify that all critical dependencies are available and functioning.
"""

from fastapi import Request
from mongoengine.connection import get_connection


async def check_nats(request: Request) -> bool:
    """Check if NATS connection is established and connected."""
    if not hasattr(request.app.state, "nc"):
        return False
    nc = request.app.state.nc
    return nc is not None and nc.is_connected


async def check_mongodb(request: Request) -> bool:
    """Check if MongoDB connection is available."""
    try:
        conn = get_connection()
        # Perform a simple command to verify connection is alive
        conn.admin.command("ping")
        return True
    except Exception:
        return False
