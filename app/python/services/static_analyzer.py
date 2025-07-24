import os
import ast
from pathlib import Path
from app.python.services.visitor import Visitor
from utils.arango import Arango


def _sanitize_key(path: str) -> str:
    return path.replace(os.sep, '_').replace('.', '_')


class StaticAnalyzer:
    def __init__(self):
        self.arango = Arango()

    def parse_python_file(self, file_path: str, parent_file_key: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code: str = f.read()
                tree = ast.parse(source=source_code, filename=file_path)
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return

        visitor = Visitor(parent_file_key=parent_file_key, source_code=source_code)
        visitor.visit(tree)

    def insert_directory_and_file_documents(self, base_dir: str):
        nodes_col = self.arango.db.collection('nodes')
        edges_col = self.arango.db.collection('edges')

        root_key = _sanitize_key(Path(base_dir).name)
        print(f'root_key ::: {root_key}')

        for root, dirs, files in os.walk(base_dir):
            rel_root = os.path.relpath(root, base_dir)
            dir_key = _sanitize_key(rel_root) if rel_root != '.' else _sanitize_key(Path(base_dir).name)

            dir_doc = {
                '_key': dir_key,
                'type': 'project_root' if root_key == dir_key else 'directory',
                'name': Path(root).name,
                'path': os.path.abspath(root)
            }
            try:
                nodes_col.insert(dir_doc, overwrite=True)
                print(f"Inserted directory: {dir_doc['path']}")
            except Exception as e:
                print(f"Failed to insert directory {dir_doc['path']}: {e}")

            parent_dir = os.path.dirname(rel_root)
            print(f'\nrel_root ::: {rel_root}, parent_dir ::: {parent_dir}\n')
            if rel_root != '.':
                parent_key = _sanitize_key(parent_dir) if parent_dir != '' else root_key
                try:
                    edges_col.insert({
                        '_from': f'nodes/{parent_key}',
                        '_to': f'nodes/{dir_key}',
                        'type': 'contains',
                        'perspective': 'directory-hierarchy'
                    })
                except Exception as e:
                    print(f"Failed to insert edge for directory {dir_key}: {e}")

            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_key = _sanitize_key(os.path.relpath(file_path, base_dir))
                file_doc = {
                    '_key': file_key,
                    'type': 'file',
                    'name': file_name,
                    'path': os.path.abspath(file_path)
                }
                try:
                    nodes_col.insert(file_doc, overwrite=True)
                    print(f"Inserted file: {file_doc['path']}")
                    edges_col.insert({
                        '_from': f'nodes/{dir_key}',
                        '_to': f'nodes/{file_key}',
                        'type': 'contains',
                        'perspective': 'file-structure'
                    })
                    if file_name.endswith('.py'):
                        self.parse_python_file(file_path=file_path, parent_file_key=file_key)
                except Exception as e:
                    print(f"Failed to insert file {file_path}: {e}")