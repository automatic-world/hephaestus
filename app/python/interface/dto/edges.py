from pydantic import BaseModel, Field


class Edges(BaseModel):
    from_: str = Field(..., alias='_from', description='id of collection: starting point of relationship')
    to_: str = Field(..., alias='_to', description='id of collection: end point of relationship')
    type: str = Field(..., alias='type', description='definition of relationship')
    perspective: str = Field(..., alias='perspective', description='explaining of relation')
    # directory-hierarchy, file-structure, class-structure, function-call