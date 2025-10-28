"""
MCP Client for MongoDB operations using OpenAI

This client connects to the MongoDB MCP server and uses OpenAI's function calling
to autonomously decide which database operations to perform.
"""

import json
import os
import pathlib
from typing import Optional, Union
from openai import OpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from dotenv import load_dotenv
from app.schemas.message import Message
import asyncio

load_dotenv()

# Global singleton instance
_global_client: Optional["MCPMongoClient"] = None
_client_lock = asyncio.Lock()


class MCPMongoClient:
    """Client for interacting with MongoDB through MCP using OpenAI."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        self._initialized = False

    async def __aenter__(self):
        """Start the MCP server and create session."""
        if not self._initialized:
            await self._initialize()
        return self

    async def _initialize(self):
        """Initialize the MCP server connection."""
        # Get the absolute path to the server script
        server_script = pathlib.Path(__file__).parent / "mongodb_server.py"

        # Pass environment variables to the MCP server subprocess
        # This ensures it has access to MONGODB_URI, MONGO_DB_NAME, etc.
        server_params = StdioServerParameters(
            command="python",
            args=[str(server_script)],
            env=os.environ.copy(),
        )

        # Store the context manager and enter it
        self._stdio_context = stdio_client(server_params)
        read_stream, write_stream = await self._stdio_context.__aenter__()

        # Create and initialize session
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()
        self._initialized = True

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up session and server."""
        # Exit in reverse order of entry
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._stdio_context:
            await self._stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def query_with_mcp(
        self, user_query: Union[str, list[Message]], max_iterations: int = 10
    ) -> dict:
        """
        Query MongoDB using MCP and OpenAI function calling.

        Args:
            user_query: The user's natural language query (string) or full chat context (list of Messages)
            max_iterations: Maximum number of tool call iterations to prevent infinite loops

        Returns:
            A dictionary containing:
            - response: The final response from OpenAI
            - pipeline: The MongoDB aggregation pipeline used (if any)
            - collection_name: The collection that was queried (if any)
            - reason: The reasoning behind the query approach
        """
        # Track pipeline information
        pipeline_info = {
            "response": "",
            "pipeline": None,
            "collection_name": None,
            "reason": "",
        }

        try:
            # List available tools from MCP server
            print("[MCP] Listing available tools...")
            tools_list = await self.session.list_tools()
            print(f"[MCP] Found {len(tools_list.tools)} tools")

            # Convert MCP tools to OpenAI function calling format
            openai_tools = []
            for tool in tools_list.tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                )

            # Initialize conversation with system prompt
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant with access to a MongoDB database. "
                        "The database contains Reddit data including threads, queries, and other collections. "
                        "Use the available tools to explore and query the database:\n"
                        "1. Start by listing collections if you're unsure what data is available\n"
                        "2. Get the schema of a collection to understand its structure\n"
                        "3. Use aggregation or find operations to query the data\n"
                        "When presenting results, format them in a clear, readable way. "
                        "If you find relevant data, include key details and summarize findings."
                    ),
                },
            ]

            # Add user query - either as a string or convert Message list to OpenAI format
            if isinstance(user_query, str):
                messages.append({"role": "user", "content": user_query})
            else:
                # Convert Message objects to OpenAI message format
                for msg in user_query:
                    messages.append({"role": msg.role.value, "content": msg.content})

            # Agentic loop - let OpenAI decide which tools to use
            iteration = 0
            while iteration < max_iterations:
                iteration += 1

                print(f"[MCP] Iteration {iteration}/{max_iterations}")

                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL_STANDARD", "gpt-4o-mini"),
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )

                response_message = response.choices[0].message

                # Check if OpenAI wants to use tools
                if response_message.tool_calls:
                    # Add assistant's message to conversation
                    messages.append(response_message)

                    # Execute each tool call
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        print(f"[MCP] Calling tool: {function_name}")
                        print(f"[MCP] Arguments: {json.dumps(function_args, indent=2)}")

                        # Capture pipeline information if this is an aggregation
                        if function_name == "aggregate_collection":
                            pipeline_info["collection_name"] = function_args.get(
                                "collection"
                            )
                            pipeline_info["pipeline"] = function_args.get("pipeline")
                            pipeline_info["reason"] = (
                                f"Used MCP aggregation on collection: {function_args.get('collection')}"
                            )
                        elif function_name == "find_documents":
                            pipeline_info["collection_name"] = function_args.get(
                                "collection"
                            )
                            # Convert find to pipeline format for consistency
                            find_filter = function_args.get("filter", {})
                            find_limit = function_args.get("limit", 10)
                            pipeline_info["pipeline"] = [
                                {"$match": find_filter},
                                {"$limit": find_limit},
                            ]
                            pipeline_info["reason"] = (
                                f"Used MCP find on collection: {function_args.get('collection')}"
                            )

                        # Call the MCP tool
                        result = await self.session.call_tool(
                            function_name, function_args
                        )

                        # Extract text content from result
                        tool_result = result.content[0].text if result.content else "{}"

                        # Add tool result to conversation
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": tool_result,
                            }
                        )
                else:
                    # No more tool calls, return the final response
                    print(
                        f"[MCP] Query completed successfully in {iteration} iterations"
                    )
                    pipeline_info["response"] = (
                        response_message.content or "No response generated"
                    )
                    return pipeline_info

            # If we hit max iterations, return what we have
            print(f"[MCP] Reached max iterations ({max_iterations})")
            pipeline_info["response"] = (
                "Query completed but may be incomplete due to iteration limit."
            )
            return pipeline_info

        except Exception as e:
            print(f"[MCP ERROR] Query failed: {str(e)}")
            import traceback

            traceback.print_exc()
            raise


async def get_mcp_client() -> MCPMongoClient:
    """
    Get or create the global MCP client instance.
    This avoids creating a new subprocess for every query.
    """
    global _global_client

    async with _client_lock:
        if _global_client is None:
            print("[MCP] Creating new global MCP client instance...")
            _global_client = MCPMongoClient()
            await _global_client._initialize()
            print("[MCP] Global MCP client initialized successfully")
        return _global_client


async def cleanup_mcp_client():
    """
    Clean up the global MCP client instance.
    Should be called on application shutdown.
    """
    global _global_client

    async with _client_lock:
        if _global_client is not None:
            print("[MCP] Cleaning up global MCP client...")
            await _global_client.__aexit__(None, None, None)
            _global_client = None
            print("[MCP] Global MCP client cleaned up")
