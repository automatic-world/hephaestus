from ast import NodeVisitor
from typing import Any
from app.python.interface.dto.control_flow import ControlFlow


class ControlVisitor(NodeVisitor):
    def __init__(self):
        self.control_flow: list[ControlFlow] = []

    def visit_if(self, node: Any):
        self.control_flow.append(ControlFlow(type='if', lineno=node.lineno))
        self.generic_visit(node)

    def visit_for(self, node: Any):
        self.control_flow.append(ControlFlow(type='for', lineno=node.lineno))
        self.generic_visit(node)

    def visit_while(self, node: Any):
        self.control_flow.append(ControlFlow(type='while', lineno=node.lineno))
        self.generic_visit(node)

    def visit_try(self, node: Any):
        self.control_flow.append(ControlFlow(type='try', lineno=node.lineno))
        self.generic_visit(node)