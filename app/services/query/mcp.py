"""
MCP Query Service

This service handles queries using the Model Context Protocol (MCP).
It allows OpenAI to autonomously query the MongoDB database using MCP tools.
"""

from typing import Dict, Any, Union
from app.mcp.client import MCPMongoClient
from app.schemas.message import Message


async def query_mcp(query: Union[str, list[Message]]) -> Dict[str, Any]:
    """
    Execute a query using MCP with OpenAI function calling.

    Args:
        query: The user's natural language query (string) or full chat context (list of Messages)

    Returns:
        A dictionary containing:
        - response: The AI-generated response based on MongoDB data
        - pipeline: The MongoDB aggregation pipeline used (if any)
        - collection_name: The collection that was queried (if any)
        - reason: The reasoning behind the query approach
    """
    async with MCPMongoClient() as mcp_client:
        result = await mcp_client.query_with_mcp(query)
        return result
