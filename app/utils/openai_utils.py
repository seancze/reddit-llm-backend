import openai
import os
import app.constants as constants
import json
import re
import sympy
from dotenv import load_dotenv
from app.schemas.mongo_pipeline_response import MongoPipelineResponse
from app.schemas.message import Message
from app.schemas.query_router_response import QueryRouterResponse, Route


load_dotenv()


def query_router(user_query: list[Message]) -> Route:
    messages = [
        {"role": "system", "content": constants.SYSTEM_PROMPT_QUERY_ROUTER},
    ] + user_query

    completion = openai.beta.chat.completions.parse(
        model="gpt-4.1-2025-04-14",
        messages=messages,
        response_format=QueryRouterResponse,
        temperature=0.2,
        top_p=0.2,
    )
    parsed_obj = completion.choices[0].message.parsed
    return parsed_obj.route


def get_mongo_pipeline(user_query: list[Message]) -> MongoPipelineResponse:
    messages = [
        {"role": "system", "content": constants.SYSTEM_PROMPT_GET_MONGODB_PIPELINE},
    ] + user_query

    completion = openai.beta.chat.completions.parse(
        # NOTE: model is hardcoded because this is the only function that uses this model
        model="gpt-4.1-2025-04-14",
        messages=messages,
        response_format=MongoPipelineResponse,
        temperature=0.2,
        top_p=0.2,
    )
    parsed_obj = completion.choices[0].message.parsed
    try:
        if parsed_obj.pipeline is not None:
            # clean each string to ensure that it is a valid JSON string
            # convert each JSON string into a dictionary
            temp = []
            for stage in parsed_obj.pipeline:
                # if starts with '#', it is a comment and should be ignored
                if stage.startswith("#"):
                    continue
                temp.append(_clean_and_parse_json_str(stage))
            parsed_obj.pipeline = temp
        return parsed_obj
    except Exception as e:
        print(f"Erroneous pipeline: {parsed_obj}")
        raise e


def get_llm_response(prompt: list[Message]):
    messages = [
        {"role": "system", "content": constants.SYSTEM_PROMPT},
    ] + prompt
    completion = openai.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL"), messages=messages
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


def _add_double_quotes_to_json_properties(json_string):
    # Regular expression to find property names without double quotes
    # Looks for: word characters followed by colon, but not already in quotes
    pattern = r'(?<!")(\b[a-zA-Z_$][a-zA-Z0-9_$]*\b)(?=\s*:)'

    # Replace with the same property name but enclosed in double quotes
    quoted_json_string = re.sub(pattern, r'"\1"', json_string)

    return quoted_json_string


def _escape_single_backslash(json_string):
    """
    Escapes only single backslashes in a string, leaving already escaped backslashes untouched.

    Args:
        text (str): The input string to process

    Returns:
        str: String with single backslashes escaped
    """
    # Process the string character by character with regex
    # (?<!\\)\\(?!\\) matches a backslash that's:
    # 1. Not preceded by another backslash (negative lookbehind)
    # 2. Not followed by another backslash (negative lookahead)
    return re.sub(r"(?<!\\)\\(?!\\)", r"\\\\", json_string)


def _evaluate_math(match):
    expr = match.group(1)
    try:
        result = float(sympy.sympify(expr).evalf())
        # Convert to int if result is a whole number
        return str(int(result) if result.is_integer() else result)
    except Exception:
        return expr


def _parse_json_with_math_expressions(json_string):
    """
    Parse a JSON string containing various mathematical expressions.
    Handles operations like +, -, *, /, **, parentheses, and more.
    """

    # Pattern for mathematical expressions
    pattern = r"(\d+(?:\s*[\+\-\*\/\^]\s*\d+)+|\(\s*[\d\+\-\*\/\s]+\))"
    processed_string = re.sub(pattern, _evaluate_math, json_string)

    return processed_string


def _clean_and_parse_json_str(json_string):
    # Clean the string by removing any leading/trailing whitespace
    json_string = json_string.strip()

    # Replace escaped newlines with actual newlines if they exist
    json_string = json_string.replace("\\n", "\n")

    # remove trailing commas
    json_string = re.sub(r",\s*}", "}", json_string)
    json_string = re.sub(r",\s*\]", "]", json_string)

    # ensure all single quotes are replaced with double quotes
    json_string = json_string.replace("'", '"')

    # ensure opening and closing braces match
    json_string = _format_braces(json_string)

    json_string = _add_double_quotes_to_json_properties(json_string)

    json_string = _escape_single_backslash(json_string)

    # evaluates mathematical expressions in JSON string
    # e.g. {"$subtract": [ "$$NOW", 7 * 24 * 60 * 60 * 1000 ]} -> {"$subtract": [ "$$NOW", 604800000 ]}
    json_string = _parse_json_with_math_expressions(json_string)

    # try to parse the JSON
    # we want the error to be raised here if the JSON is invalid
    return json.loads(json_string)
