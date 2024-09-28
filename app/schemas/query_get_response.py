from app.schemas.query_post_response import QueryPostResponse


class QueryGetResponse(QueryPostResponse):
    is_chat_owner: bool
