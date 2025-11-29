import re
from app.schemas.message import Message


def normalise_query(query: list[Message]):
    for i in range(len(query)):
        query[i].content = re.sub(r"\s+", " ", query[i].content.strip().lower())
    return query
