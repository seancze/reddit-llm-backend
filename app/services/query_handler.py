import openai
from app import constants
from app.db.conn import mongodb_connection
from app.utils.vector_search import vector_search
from app.utils.mongodb_query import get_mongodb_query, query_mongodb


def handle_user_query(query):
    mongo_query = get_mongodb_query(query)
    print(f"mongo_query: {mongo_query} type: {type(mongo_query)}")

    # if the pipeline is None, it means that we are not supposed to query the database
    # hence, we set vector search to True
    use_vector_search = mongo_query["pipeline"] is None
    prompt = f"""User Query:
{query}

Data from database:"""

    data = None

    if mongo_query["pipeline"]:
        mongodb_data = query_mongodb(
            mongo_query["collection_name"], mongo_query["pipeline"]
        )
        print(f"mongodb_data: {mongodb_data}")
        # if the data returned is empty we should use vector search
        if len(mongodb_data) == 0:
            use_vector_search = True
        else:
            prompt += f"""\n{mongodb_data}\nDatabase query: {mongo_query["pipeline"]}"""
        data = mongodb_data
    if use_vector_search:
        with mongodb_connection() as conn:
            collection = conn.db["thread"]

            get_knowledge = vector_search(query, collection)

            search_result = ""

            for i, result in enumerate(get_knowledge):
                thread_id = result.get("id")
                # for each thread_id, get the top 5 comments from the 'comment' collection based on the score and add them to the search result
                comments = (
                    conn.db["comment"]
                    .find(
                        {
                            "parent_id": f"t3_{thread_id}"  # we use parent_id to ensure that we only get top-level comments
                        },
                        {"_id": 0, "score": 1, "body": 1},
                    )
                    .sort([("score", -1)])
                    .limit(3)
                )

                # ensure that the comments are formatted like this: "Comment (Score: {score}): {body} \n"
                comments_str = " \n".join(
                    [
                        f"Comment (Score: {comment.get('score', 'N/A')}): {comment.get('body', 'N/A')}"
                        for comment in comments
                    ]
                )

                search_result += f"""Thread {i+1} (Score: {result.get('score', 'N/A')})\nTitle: {result.get('title', 'N/A')}\nURL: https://reddit.com{result.get('permalink', 'N/A')}\nBody: {result.get('selftext', "N/A")}\n{comments_str}\n\n\n"""
                # print(f"search_result: {search_result}")
                data = search_result

            prompt += f"""\n{search_result}"""

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": constants.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return completion.choices[0].message.content, data
