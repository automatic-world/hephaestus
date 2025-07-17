from pydantic import BaseModel, Field

from app.python.interface.dto.instance_variables import InstanceVariables


class Nodes(BaseModel):
    key: str = Field(..., alias='_key', description='key of the Collection')
    type: str = Field(..., alias='type', description='type of objects')
    name: str = Field(..., alias='name', description='name of function or class')
    defined_in: str = Field(..., alias='defined_in', description='the module where the function is defined')
    lineno: int = Field(..., alias='lineno', description='the number at which the line begins')
    docstring: str = Field(..., alias='docstring', description='comments written by developers')
    source: str = Field(..., alias='full content of functions')
    inst_variables: InstanceVariables | None = Field(..., alias='inst_variables', description="information of instance's variables")
