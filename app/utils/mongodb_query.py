import openai
import json
import os
import app.constants as constants
from app.db.conn import MongoDBConnection
from dotenv import load_dotenv

load_dotenv()


def query_mongodb(collection_name: str, pipeline: list, db_conn: MongoDBConnection):

    collection = db_conn.get_collection(collection_name)

    if collection_name == "thread":
        # Add a $project stage to exclude selftext_embedding at the beginning of the pipeline
        pipeline.insert(0, {"$project": {"selftext_embedding": 0, "_id": 0}})

    # Execute the aggregation pipeline
    documents = list(collection.aggregate(pipeline))

    return documents


def get_mongo_pipeline(user_query):

    response = openai.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": constants.SYSTEM_PROMPT_GET_MONGODB_QUERY},
            {
                "role": "user",
                "content": f"{user_query}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        top_p=0.2,
    )

    return json.loads(response.choices[0].message.content)
