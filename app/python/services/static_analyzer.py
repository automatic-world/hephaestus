import os
import ast
from pathlib import Path
from app.python.interface.dto.edges import Edges
from app.python.interface.dto.nodes import Nodes
from app.python.services.visitor import Visitor
from utils.arango import Arango


def _sanitize_key(path: str) -> str:
    return path.replace(os.sep, '_').replace('.', '_')


class StaticAnalyzer:
    def __init__(self):
        self.arango = Arango()

    def parse_python_file(self, file_path: str, parent_file_key: str) -> tuple[list[Nodes], list[Edges]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code: str = f.read()
                tree = ast.parse(source=source_code, filename=file_path)
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return [], []

        visitor = Visitor(parent_file_key=parent_file_key, source_code=source_code)
        visitor.visit(node=tree)

        return visitor.nodes, visitor.edges

    def insert_directory_and_file_documents(self, base_dir: str):
        _nodes: list[Nodes] = []
        _edges: list[Edges] = []

        root_key = _sanitize_key(path=Path(base_dir).name)
        print(f'root_key ::: {root_key}')

        for root, dirs, files in os.walk(top=base_dir):
            rel_root = os.path.relpath(path=root, start=base_dir)
            dir_key = _sanitize_key(path=rel_root) if rel_root != '.' else _sanitize_key(path=Path(base_dir).name)

            _nodes.append(
                Nodes(
                    _key=dir_key,
                    type='project_root' if root_key == dir_key else 'directory',
                    name=Path(root).name,
                    path=os.path.abspath(path=root)
                )
            )

            parent_dir = os.path.dirname(p=rel_root)
            print(f'\nrel_root ::: {rel_root}, parent_dir ::: {parent_dir}\n')
            if rel_root != '.':
                parent_key = _sanitize_key(path=parent_dir) if parent_dir != '' else root_key
                _edges.append(
                    Edges(
                        _from=f'nodes/{parent_key}',
                        _to=f'nodes/{dir_key}',
                        type='contains',
                        perspective='directory-hierarchy'
                    )
                )

            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_key = _sanitize_key(path=os.path.relpath(path=file_path, start=base_dir))
                _nodes.append(
                    Nodes(
                        _key=file_key,
                        type='file',
                        name=file_name,
                        path=os.path.abspath(path=file_path)
                    )
                )
                _edges.append(
                    Edges(
                        _from=f'nodes/{dir_key}',
                        _to=f'nodes/{file_key}',
                        type='contains',
                        perspective='file-structure'
                    )
                )
                if file_name.endswith('.py'):
                    _n, _e = self.parse_python_file(file_path=file_path, parent_file_key=file_key)
                    _nodes += _n
                    _edges += _e