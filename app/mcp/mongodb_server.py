"""
MongoDB MCP Server

This server exposes MongoDB operations as MCP tools that can be called by AI models.
"""

import asyncio
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

app = Server("mongodb-mcp-server")

# MongoDB connection
mongodb_uri = os.environ.get("MONGODB_URI")
mongo_db_name = os.environ.get("MONGO_DB_NAME")

if not mongodb_uri or not mongo_db_name:
    raise ValueError(
        "MONGODB_URI and MONGO_DB_NAME must be set in environment variables"
    )

client: MongoClient = MongoClient(mongodb_uri)
db = client[mongo_db_name]


def serialize_bson(obj):
    """Convert BSON types to JSON-serializable types."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_bson(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_bson(item) for item in obj]
    return obj


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MongoDB tools."""
    return [
        types.Tool(
            name="list_collections",
            description=(
                "List all available collections in the MongoDB database. "
                "Use this first to discover what data is available before querying."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="aggregate_collection",
            description=(
                "Execute a MongoDB aggregation pipeline on any collection. "
                "Use this to perform complex queries like filtering, sorting, grouping, "
                "and computing statistics. Returns matching documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Name of the collection to query (e.g., 'thread', 'query')",
                    },
                    "pipeline": {
                        "type": "array",
                        "description": (
                            "MongoDB aggregation pipeline as a JSON array of stage objects. "
                            "Example: [{'$match': {'score': {'$gt': 100}}}, {'$limit': 10}]"
                        ),
                        "items": {
                            "type": "object",
                            "description": "A single pipeline stage",
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["collection", "pipeline"],
            },
        ),
        types.Tool(
            name="find_documents",
            description=(
                "Find documents in any collection using a simple MongoDB find query. "
                "Use this for straightforward filtering without aggregation. "
                "Supports basic filters and limit."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Name of the collection to query (e.g., 'thread', 'query')",
                    },
                    "filter": {
                        "type": "object",
                        "description": (
                            "MongoDB filter query object. "
                            "Example: {'score': {'$gt': 100}, 'subreddit': 'python'}"
                        ),
                        "additionalProperties": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["collection", "filter"],
            },
        ),
        types.Tool(
            name="get_collection_schema",
            description=(
                "Get information about the structure and available fields in a collection. "
                "Useful for understanding what fields can be queried. "
                "Returns a sample document showing the schema."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Name of the collection to inspect (e.g., 'thread', 'query')",
                    },
                },
                "required": ["collection"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute MongoDB operations."""
    try:
        if name == "list_collections":
            # List all collections in the database
            collections = db.list_collection_names()

            collection_info = {
                "database": mongo_db_name,
                "collections": collections,
                "count": len(collections),
            }

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(collection_info, indent=2, ensure_ascii=False),
                )
            ]

        elif name == "aggregate_collection":
            collection_name = arguments["collection"]
            pipeline = arguments["pipeline"]

            # Validate collection exists
            if collection_name not in db.list_collection_names():
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Collection '{collection_name}' not found",
                                "available_collections": db.list_collection_names(),
                            },
                            indent=2,
                        ),
                    )
                ]

            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))

            # Convert BSON types to JSON-serializable
            results = serialize_bson(results)

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, indent=2, ensure_ascii=False),
                )
            ]

        elif name == "find_documents":
            collection_name = arguments["collection"]
            filter_query = arguments["filter"]
            limit = arguments.get("limit", 10)

            # Validate collection exists
            if collection_name not in db.list_collection_names():
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Collection '{collection_name}' not found",
                                "available_collections": db.list_collection_names(),
                            },
                            indent=2,
                        ),
                    )
                ]

            collection = db[collection_name]
            results = list(collection.find(filter_query).limit(limit))

            # Convert BSON types to JSON-serializable
            results = serialize_bson(results)

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, indent=2, ensure_ascii=False),
                )
            ]

        elif name == "get_collection_schema":
            collection_name = arguments["collection"]

            # Validate collection exists
            if collection_name not in db.list_collection_names():
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Collection '{collection_name}' not found",
                                "available_collections": db.list_collection_names(),
                            },
                            indent=2,
                        ),
                    )
                ]

            # Get a sample document to show the schema
            collection = db[collection_name]
            sample = collection.find_one()

            if sample:
                sample = serialize_bson(sample)
                schema_info = {
                    "collection": collection_name,
                    "sample_fields": list(sample.keys()),
                    "sample_document": sample,
                    "document_count": collection.count_documents({}),
                }
            else:
                schema_info = {
                    "collection": collection_name,
                    "message": "No documents found in collection",
                    "document_count": 0,
                }

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(schema_info, indent=2, ensure_ascii=False),
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        error_msg = {
            "error": str(e),
            "type": type(e).__name__,
        }
        return [
            types.TextContent(
                type="text",
                text=json.dumps(error_msg, indent=2),
            )
        ]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
