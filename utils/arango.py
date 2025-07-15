from arango import ArangoClient
from arango.database import StandardDatabase


class Arango:
    def __init__(self):
        self.client: ArangoClient = ArangoClient()
        self.db: StandardDatabase = self.client.db(name='_system', username='root', password='openSesame')

    def create_collection_if_not_exists(self, name: str, is_edge: bool) -> None:
        if not self.is_collection_exists(name=name):
            self.db.create_collection(name=name, edge=is_edge)
            print(f"Collection has created: {name}")

    def delete_collection(self, name: str) -> None:
        if self.is_collection_exists(name=name):
            self.db.delete_collection(name=name)
            print(f"Collection has deleted: {name}")

    def is_collection_exists(self, name: str) -> bool:
        return self.db.has_collection(name=name)

    def is_view_exists(self, name: str) -> bool:
        try:
            self.db.view(name)
            return True
        except Exception:
            return False