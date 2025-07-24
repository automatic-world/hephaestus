from ast import NodeVisitor, AST
from app.python.interface.dto.control_flow import ControlFlow


class ControlVisitor(NodeVisitor):
    def __init__(self):
        self.control_flow: list[ControlFlow] = []

    def visit_If(self, node: AST):
        self.control_flow.append(ControlFlow(type='if', lineno=node.lineno))
        self.generic_visit(node=node)

    def visit_For(self, node: AST):
        self.control_flow.append(ControlFlow(type='for', lineno=node.lineno))
        self.generic_visit(node=node)

    def visit_While(self, node: AST):
        self.control_flow.append(ControlFlow(type='while', lineno=node.lineno))
        self.generic_visit(node=node)

    def visit_Try(self, node: AST):
        self.control_flow.append(ControlFlow(type='try', lineno=node.lineno))
        self.generic_visit(node=node)