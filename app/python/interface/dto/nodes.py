from pydantic import BaseModel, Field
from app.python.interface.dto.arg import Arg
from app.python.interface.dto.control_flow import ControlFlow
from app.python.interface.dto.instance_variables import InstanceVariables


class Nodes(BaseModel):
    key: str = Field(..., alias='_key', description='key of the Collection')
    type: str = Field(..., alias='type', description='type of objects')
    name: str = Field(..., alias='name', description='name of function or class')
    path: str | None = Field(default=None, alias='path', description='the location of directory')
    defined_in: str | None = Field(default=None, alias='defined_in', description='the module where the function is defined')
    lineno: int | None = Field(default=None, alias='lineno', description='the number at which the line begins')
    docstring: str | None = Field(default=None, alias='docstring', description='comments written by developers')
    source: str | None = Field(default=None, alias='source', description='full content of functions')
    inst_variables: list[InstanceVariables] | None = Field(default=None, alias='inst_variables', description="information of instance's variables")
    args: list[Arg] | None = Field(default=None, alias='args', description='Arguments of the function')
    return_type: str | None = Field(default=None, alias='return_type', description='return type of the function')
    control_flow: list[ControlFlow] | None = Field(default=None, alias='control_flow', description='control flows of the function')
