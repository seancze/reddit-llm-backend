from typing import List, Optional
from pydantic import BaseModel


class MongoPipelineResponse(BaseModel):
    pipeline: List[str]
    collection_name: Optional[str]
    reason: str
