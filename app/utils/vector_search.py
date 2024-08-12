from app.utils.preprocess import get_embedding


# TODO: Perhaps, before doing a vector search, we first filter for those with at least x number of upvotes?
# TODO: Alternatively, do vector search first THEN filter for upvotes?
def vector_search(user_query, collection):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.

    Returns:
    list: A list of matching documents.
    """
    print(f"user_query: {user_query}")
    # Generate embedding for the user query
    query_embedding = get_embedding(user_query)

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
                "vector_search_score": {
                    "$meta": "vectorSearchScore"
                },  # Include the search score
            }
        },
    ]

    # Execute the search
    results = collection.aggregate(pipeline)
    return list(results)
