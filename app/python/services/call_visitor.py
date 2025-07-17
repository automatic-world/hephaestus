from ast import NodeVisitor, Call, Name


class CallVisitor(NodeVisitor):
    def __init__(self, func_start: int, func_end: int):
        self.func_start: int = func_start
        self.func_end: int = func_end
        self.calls: list[str] = []

    def visit_call(self, node: Call):
        if self.func_start <= node.lineno <= self.func_end:
            if isinstance(node.func, Name):
                self.calls.append(node.func.id)
        self.generic_visit(node=node)