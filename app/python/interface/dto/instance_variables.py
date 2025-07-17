from pydantic import BaseModel, Field


class InstanceVariables(BaseModel):
    var: str | None = Field(..., alias='var', description='name of variable')
    type: str | None = Field(..., alias='type', description='data type')
    value: str | None = Field(..., alias='value', description='value')
    lineno: int | None = Field(..., alias='lineno', description='line number')