from pydantic import BaseModel, Field


class CollectionStatus(BaseModel):
    collection: str = Field(..., alias="collection", description="Arango Collection명")
    is_edge: bool = Field(..., alias="is_edge", description="edge 여부")