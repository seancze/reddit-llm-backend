from pydantic import BaseModel, Field


class MCPQueryRequest(BaseModel):
    """Request model for MCP-based queries."""

    query: str = Field(
        ...,
        description="Natural language query about Reddit threads",
        min_length=1,
    )

    class Config:
        json_schema_extra = {
            "example": {"query": "Find me the top 5 most upvoted threads about Python"}
        }
