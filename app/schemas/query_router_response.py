from pydantic import BaseModel
from app.schemas.route import Route


class QueryRouterResponse(BaseModel):
    route: Route
