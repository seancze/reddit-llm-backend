"""
MCP Lifespan Manager

Handles initialization and cleanup of the MCP client during FastAPI application lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.mcp.client import get_mcp_client, cleanup_mcp_client


@asynccontextmanager
async def mcp_lifespan(app: FastAPI):
    """
    Initialize MCP client on startup and clean up on shutdown.

    This ensures the MCP server subprocess is created once and reused
    for all requests, avoiding the overhead of creating a new subprocess
    for each query.
    """
    # Initialize MCP client on startup
    try:
        await get_mcp_client()
        print("MCP client initialized during startup")
    except Exception as e:
        print(f"Warning: Failed to initialize MCP client during startup: {e}")

    yield

    # Clean up MCP client on shutdown
    try:
        await cleanup_mcp_client()
    except Exception as e:
        print(f"Warning: Failed to cleanup MCP client: {e}")
