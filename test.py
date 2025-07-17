import os
import ast
from arango import ArangoClient
from arango.database import StandardDatabase
from pathlib import Path

def get_db_connection() -> StandardDatabase:
    client = ArangoClient()
    db = client.db('_system', username='root', password='openSesame')
    return db

def create_collections(db: StandardDatabase):
    collections = [
        ('nodes', False),
        ('edges', True)
    ]
    for name, is_edge in collections:
        if not db.has_collection(name):
            db.create_collection(name, edge=is_edge)
            print(f"Created collection: {name}")
        else:
            print(f"Collection already exists: {name}, delete and recreate")
            db.delete_collection(name)
            db.create_collection(name, edge=is_edge)

def sanitize_key(path: str) -> str:
    return path.replace(os.sep, '_').replace('.', '_')

def parse_python_file(file_path: str, parent_file_key: str, db: StandardDatabase):
    nodes_col = db.collection('nodes')
    edges_col = db.collection('edges')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            tree = ast.parse(source_code, filename=file_path)
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return

    class CallVisitor(ast.NodeVisitor):
        def __init__(self, func_start, func_end):
            self.func_start = func_start
            self.func_end = func_end
            self.calls = []

        def visit_Call(self, node: ast.Call):
            if self.func_start <= node.lineno <= self.func_end:
                if isinstance(node.func, ast.Name):
                    self.calls.append(node.func.id)
            self.generic_visit(node)

    class ControlVisitor(ast.NodeVisitor):
        def __init__(self):
            self.control_flow = []

        def visit_If(self, node):
            self.control_flow.append({'type': 'if', 'lineno': node.lineno})
            self.generic_visit(node)

        def visit_For(self, node):
            self.control_flow.append({'type': 'for', 'lineno': node.lineno})
            self.generic_visit(node)

        def visit_While(self, node):
            self.control_flow.append({'type': 'while', 'lineno': node.lineno})
            self.generic_visit(node)

        def visit_Try(self, node):
            self.control_flow.append({'type': 'try', 'lineno': node.lineno})
            self.generic_visit(node)

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef):
            class_key = f"{parent_file_key}_{node.name}"

            # 1. __init__ 함수에서 self.xxx = ... 만 추출하여 배열로 저장
            inst_variables = []
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    for subnode in ast.walk(stmt):
                        if isinstance(subnode, ast.Assign):
                            for target in subnode.targets:
                                if (isinstance(target, ast.Attribute) and
                                        isinstance(target.value, ast.Name) and
                                        target.value.id == 'self'):
                                    var_name = target.attr
                                    var_type = None  # 타입 힌트가 있을 경우 추출, 기본은 None
                                    # 변수에 type hint가 있다면 추출 (Python 3.8+)
                                    if hasattr(target, 'annotation') and target.annotation:
                                        try:
                                            var_type = ast.unparse(target.annotation).strip()
                                        except Exception:
                                            pass
                                    # 변수에 할당된 값이 있다면 문자열로 저장
                                    var_value = ast.unparse(ast_obj=subnode.value).strip() if hasattr(ast, 'unparse') else None
                                    inst_variables.append({
                                        'var': var_name,
                                        'type': var_type,
                                        'value': var_value,
                                        'lineno': subnode.lineno
                                    })

            class_doc = {
                '_key': class_key,
                'type': 'class',
                'name': node.name,
                'defined_in': parent_file_key,
                'lineno': node.lineno,
                'docstring': ast.get_docstring(node),
                'source': ast.get_source_segment(source_code, node),
                'inst_variables': inst_variables
            }
            try:
                nodes_col.insert(class_doc, overwrite=True)
                edges_col.insert({
                    '_from': f'nodes/{parent_file_key}',
                    '_to': f'nodes/{class_key}',
                    'type': 'defines',
                    'perspective': 'class-structure'
                })
                print(f"Inserted class: {node.name} in {file_path}")
            except Exception as e:
                print(f"Failed to insert class {node.name}: {e}")
            self.generic_visit(node)


        def visit_FunctionDef(self, node: ast.FunctionDef):
            func_key = f"{parent_file_key}_{node.name}"
            func_code = ast.get_source_segment(source_code, node)
            docstring = ast.get_docstring(node)

            args = []
            for arg in node.args.args:
                arg_name = arg.arg
                arg_type = ast.unparse(arg.annotation).strip() if arg.annotation else None
                args.append({'arg': arg_name, 'type': arg_type})

            return_type = ast.unparse(node.returns).strip() if node.returns else None

            control_visitor = ControlVisitor()
            control_visitor.visit(node)

            func_doc = {
                '_key': func_key,
                'type': 'function',
                'name': node.name,
                'defined_in': parent_file_key,
                'lineno': node.lineno,
                'source': func_code,
                'docstring': docstring,
                'args': args,
                'return_type': return_type,
                'control_flow': control_visitor.control_flow
            }
            try:
                nodes_col.insert(func_doc, overwrite=True)
                edges_col.insert({
                    '_from': f'nodes/{parent_file_key}',
                    '_to': f'nodes/{func_key}',
                    'type': 'defines',
                    'perspective': 'function-structure'
                })
                print(f"Inserted function: {node.name} in {file_path}")

                func_start = node.lineno
                func_end = max([
                    child.lineno for child in ast.walk(node)
                    if hasattr(child, 'lineno')
                ], default=func_start)

                call_visitor = CallVisitor(func_start, func_end)
                call_visitor.visit(node)
                for callee_name in call_visitor.calls:
                    callee_key = f"{parent_file_key}_{callee_name}"
                    try:
                        edges_col.insert({
                            '_from': f'nodes/{func_key}',
                            '_to': f'nodes/{callee_key}',
                            'type': 'calls',
                            'perspective': 'function-call'
                        })
                        print(f"  ↳ {func_key} calls {callee_key}")
                    except Exception as e:
                        print(f"Failed to insert call edge {func_key} → {callee_key}: {e}")
            except Exception as e:
                print(f"Failed to insert function {node.name}: {e}")

    visitor = Visitor()
    visitor.visit(tree)

def insert_directory_and_file_documents(db: StandardDatabase, base_dir: str):
    nodes_col = db.collection('nodes')
    edges_col = db.collection('edges')

    root_key = sanitize_key(Path(base_dir).name)
    print(f'root_key ::: {root_key}')

    for root, dirs, files in os.walk(base_dir):
        rel_root = os.path.relpath(root, base_dir)
        dir_key = sanitize_key(rel_root) if rel_root != '.' else sanitize_key(Path(base_dir).name)

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
        # if parent_dir != "" and rel_root != '.':
        if rel_root != '.':
            parent_key = sanitize_key(parent_dir) if parent_dir != '' else root_key
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
            file_key = sanitize_key(os.path.relpath(file_path, base_dir))
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
                    parse_python_file(file_path, file_key, db)
            except Exception as e:
                print(f"Failed to insert file {file_path}: {e}")

def main():
    base_dir = "C:\\workspace\\langchain-neo4j"  # TODO: replace with your actual project directory
    db = get_db_connection()
    create_collections(db)
    insert_directory_and_file_documents(db, base_dir)

if __name__ == "__main__":
    main()
