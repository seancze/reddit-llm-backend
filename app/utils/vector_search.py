import os
from dotenv import load_dotenv
from app.schemas.message import Message
from pymongo.collection import Collection
from openai import AsyncOpenAI
from fastapi.concurrency import run_in_threadpool

load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"


# TODO: Perhaps, before doing a vector search, we first filter for those with at least x number of upvotes?
# TODO: Alternatively, do vector search first THEN filter for upvotes?
async def vector_search(user_query: list[Message], collection: Collection):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.

    Returns:
    list: A list of matching documents.
    """
    # print(f"user_query: {user_query}")
    user_query_str = "\n".join([msg.content for msg in user_query])
    # Generate embedding for the user query
    query_embedding = await _get_embedding(user_query_str)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "selftext_vector_index",
                "queryVector": query_embedding,
                "path": "selftext_embedding",
                "numCandidates": 150,  # Number of candidate matches to consider
                "limit": 3,
                # "filter": {"score": {"$gt": 500}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "title": 1,
                "score": 1,
                "selftext": 1,
                "permalink": 1,
                "created_utc": 1,
                "vector_search_score": {
                    "$meta": "vectorSearchScore"
                },  # Include the search score
            }
        },
    ]

    # Execute the search
    results = await run_in_threadpool(lambda: list(collection.aggregate(pipeline)))
    return results


async def _get_embedding(text):
    """Generate an embedding for the given text using OpenAI's API."""

    # Check for valid input
    if not text or not isinstance(text, str):
        return None

    try:
        # Call OpenAI API to get the embedding
        response = await client.embeddings.create(input=text, model=EMBEDDING_MODEL)
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        raise e
        # print(f"Error in get_embedding: {e}")
        # return None
