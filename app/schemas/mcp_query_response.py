from pydantic import BaseModel, Field


class MCPQueryResponse(BaseModel):
    """Response model for MCP-based queries."""

    response: str = Field(
        ...,
        description="The AI-generated response based on MongoDB data",
    )
    method: str = Field(
        default="mcp",
        description="The query method used (always 'mcp' for this endpoint)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Here are the top 5 most upvoted Python threads...",
                "method": "mcp",
            }
        }
