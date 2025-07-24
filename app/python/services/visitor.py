from ast import AST, NodeVisitor, ClassDef, FunctionDef, walk, Assign, Attribute, Name, \
    unparse, get_docstring, get_source_segment
import ast
from typing import Any
from app.python.interface.dto.arg import Arg
from app.python.interface.dto.edges import Edges
from app.python.interface.dto.instance_variables import InstanceVariables
from app.python.interface.dto.nodes import Nodes
from app.python.services.call_visitor import CallVisitor
from app.python.services.control_visitor import ControlVisitor


class Visitor(NodeVisitor):
    def __init__(
        self,
        parent_file_key: str,
        source_code: str
    ):
        self.parent_file_key = parent_file_key
        self.source_code = source_code
        self.edges: list[Edges] = []
        self.nodes: list[Nodes] = []

    def visit_ClassDef(self, node: ClassDef) -> None:
        class_key = f"{self.parent_file_key}_{node.name}"

        # 1. __init__ 함수에서 self.xxx = ... 만 추출하여 배열로 저장
        inst_variables: list[InstanceVariables] = []
        for stmt in node.body:
            if isinstance(stmt, FunctionDef) and stmt.name == "__init__":
                for subnode in walk(node=stmt):
                    if isinstance(subnode, Assign):
                        for target in subnode.targets:
                            if (isinstance(target, Attribute) and
                                    isinstance(target.value, Name) and
                                    target.value.id == 'self'):
                                var_name = target.attr
                                var_type = None  # 타입 힌트가 있을 경우 추출, 기본은 None
                                # 변수에 type hint가 있다면 추출 (Python 3.8+)
                                if hasattr(target, 'annotation') and target.annotation:
                                    try:
                                        var_type = unparse(target.annotation).strip()
                                    except Exception:
                                        pass
                                # 변수에 할당된 값이 있다면 문자열로 저장
                                var_value = unparse(ast_obj=subnode.value).strip() if hasattr(ast, 'unparse') else None
                                inst_variables.append(
                                    InstanceVariables(
                                        var=var_name,
                                        type=var_type,
                                        value=var_value,
                                        lineno=subnode.lineno
                                    )
                                )

        self.nodes.append(
            Nodes(
                _key=class_key,
                type='class',
                name=node.name,
                defined_in=self.parent_file_key,
                lineno=node.lineno,
                docstring=get_docstring(node=node),
                source=get_source_segment(source=self.source_code, node=node),
                inst_variables=inst_variables
            )
        )

        self.edges.append(
            Edges(
                _from=f'nodes/{self.parent_file_key}',
                _to=f'nodes/{class_key}',
                type='defines',
                perspective='class-structure'
            )
        )
        self.generic_visit(node=node)

    def visit_FunctionDef(self, node: FunctionDef):
        func_key = f"{self.parent_file_key}_{node.name}"
        func_code = get_source_segment(self.source_code, node)
        docstring = get_docstring(node)

        _nodes: list[Nodes] = []
        _edges: list[Edges] = []

        args: list[Arg] = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = unparse(ast_obj=arg.annotation).strip() if arg.annotation else None
            args.append(
                Arg(
                    arg=arg_name,
                    type=arg_type
                )
            )

        return_type = unparse(ast_obj=node.returns).strip() if node.returns else None

        control_visitor = ControlVisitor()
        control_visitor.visit(node)

        self.nodes.append(
            Nodes(
                _key=func_key,
                type='function',
                name=node.name,
                defined_in=self.parent_file_key,
                lineno=node.lineno,
                source=func_code,
                docstring=docstring,
                args=args,
                return_type=return_type,
                control_flow=control_visitor.control_flow
            )
        )

        self.edges.append(
            Edges(
                _from=f'nodes/{self.parent_file_key}',
                _to=f'nodes/{func_key}',
                type='defines',
                perspective='function-structure'
            )
        )

        func_start = node.lineno
        func_end = max([child.lineno for child in walk(node) if hasattr(child, 'lineno')], default=func_start)

        call_visitor = CallVisitor(func_start, func_end)
        call_visitor.visit(node)

        for callee_name in call_visitor.calls:
            callee_key = f"{self.parent_file_key}_{callee_name}"
            self.edges.append(
                Edges(
                    _from=f'nodes/{func_key}',
                    _to=f'nodes/{callee_key}',
                    type='calls',
                    perspective='function-call'
                )
            )

    def visit(self, node: AST) -> Any:
        return self.visit(node=node)