import openai
import json
import os
import app.constants as constants
from dotenv import load_dotenv

load_dotenv()


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


def get_llm_response(prompt):
    completion = openai.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": constants.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return completion.choices[0].message.content
