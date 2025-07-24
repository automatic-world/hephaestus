from pydantic import BaseModel, Field


class CollectionInformation(BaseModel):
    collection: str = Field(..., alias='collection', description='name of collection')
    data: list[dict] | None = Field(default=None, alias='data', description='documents of collection')
    is_edge: bool | None = Field(default=False, alias='is_edge', description='whether document or edge')