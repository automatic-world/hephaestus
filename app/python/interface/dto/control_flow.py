from pydantic import BaseModel, Field


class ControlFlow(BaseModel):
    type: str = Field(..., alias="type", description="분기문 조건")
    lineno: int = Field(..., alias="lineno", description="줄 번호")