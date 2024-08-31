import openai
import os
import app.constants as constants
import json
import re
from dotenv import load_dotenv
from app.schemas.mongo_pipeline_response import MongoPipelineResponse


load_dotenv()


def get_mongo_pipeline(user_query: str) -> MongoPipelineResponse:

    completion = openai.beta.chat.completions.parse(
        # NOTE: hardcode the model for now as this is the only gpt4o model that supports structured outputs
        # see here for more information: https://platform.openai.com/docs/guides/structured-outputs/introduction
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": constants.SYSTEM_PROMPT_GET_MONGODB_PIPELINE},
            {
                "role": "user",
                "content": f"{user_query}",
            },
        ],
        response_format=MongoPipelineResponse,
        temperature=0.2,
        top_p=0.2,
    )
    parsed_obj = completion.choices[0].message.parsed
    try:
        if parsed_obj.pipeline is not None:
            # clean each string to ensure that it is a valid JSON string
            # convert each JSON string into a dictionary
            parsed_obj.pipeline = [
                _clean_and_parse_json_str(stage) for stage in parsed_obj.pipeline
            ]

        return parsed_obj
    except Exception as e:
        print(f"Erroneous pipeline: {parsed_obj}")
        raise e


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


def _format_braces(json_string):
    stack = []
    brace_pairs = {"}": "{", "]": "[", ")": "("}
    opening_braces = set(brace_pairs.values())
    corrected = []
    missing_closing = []

    for char in json_string:
        if char in opening_braces:
            stack.append(char)
            corrected.append(char)
        elif char in brace_pairs:
            if not stack:
                # if there is an extra closing brace, skip this closing brace
                continue
            if stack[-1] != brace_pairs[char]:
                # if the current closing brace does not match the last opening brace
                found = False
                for i in range(len(stack) - 1, -1, -1):
                    # find the matching opening brace in reverse order
                    if stack[i] == brace_pairs[char]:
                        # once the matching opening brace is found, close all opening braces that come after it
                        while len(stack) > i:
                            missing_closing.append(
                                next(
                                    k
                                    for k, v in brace_pairs.items()
                                    if v == stack.pop()
                                )
                            )
                        # finally, set found to True to add the current closing brace to corrected (see below)
                        found = True
                        break
                if not found:
                    # no matching opening brace found, skip this closing brace
                    continue
            else:
                stack.pop()
            corrected.append(char)
        else:
            corrected.append(char)

    # close any remaining open braces
    while stack:
        missing_closing.append(
            next(k for k, v in brace_pairs.items() if v == stack.pop())
        )

    corrected_string = "".join(corrected + missing_closing)
    return corrected_string


def _clean_and_parse_json_str(json_string):
    # remove trailing commas
    json_string = re.sub(r",\s*}", "}", json_string)
    json_string = re.sub(r",\s*\]", "]", json_string)

    # ensure all single quotes are replaced with double quotes
    json_string = json_string.replace("'", '"')

    # ensure opening and closing braces match
    json_string = _format_braces(json_string)

    # try to parse the JSON
    # we want the error to be raised here if the JSON is invalid
    return json.loads(json_string)
