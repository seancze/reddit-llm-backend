import re
from datetime import datetime, timezone
from app.db.conn import MongoDBConnection


def normalise_query(query):
    return re.sub(r"\s+", " ", query.strip().lower())


def format_vector_search_result(db_conn: MongoDBConnection, vector_search_result: list):
    comment_collection = db_conn.get_collection("comment")
    search_result = ""

    for i, result in enumerate(vector_search_result):
        thread_id = result.get("id")
        # for each thread_id, get the top 5 comments from the 'comment' collection based on the score and add them to the search result
        comments = (
            comment_collection.find(
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

    return search_result


def get_human_readable_datetime(utc_timestamp: int):
    # convert the UTC timestamp to a datetime object
    dt = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)

    # the formatted date should look like "Aug 31 2024, 08:15PM"
    formatted_date = dt.strftime("%b %d %Y, %I:%M%p")

    return formatted_date
