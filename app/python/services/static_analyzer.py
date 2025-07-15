import os
import ast
from arango import ArangoClient
from arango.database import StandardDatabase
from pathlib import Path
from utils.arango import Arango


class StaticAnalyzer:
    def __init__(self):
        self.arango = Arango()

    def sanitize_key(self, path: str) -> str:
        return path.replace(os.sep, '_').replace('.', '_')

    def parse_python_file(self, file_path: str):

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                tree = ast.parse(source_code, filename=file_path)
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return