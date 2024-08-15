import re


def normalise_query(query):
    return re.sub(r"\s+", " ", query.strip().lower())
