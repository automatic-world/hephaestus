from typing import Iterator

from arango import ArangoClient, ViewGetError, AnalyzerGetError, CollectionDeleteError, CollectionCreateError, \
    DocumentInsertError
from arango.database import StandardDatabase
from app.graph.interface.dto.arango.collection_information import CollectionInformation


class Arango:
    def __init__(self):
        self.client: ArangoClient = ArangoClient()
        self.db: StandardDatabase = self.client.db(name='_system', username='root', password='openSesame')

    def create_collection(self, name: str, is_edge: bool) -> bool:
        try:
            if not self.is_collection_existed(name=name):
                self.db.create_collection(name=name, edge=is_edge)
                print(f"Collection has created: {name}")
            else:
                print(f"Collection already exists: {name}")
            return True
        except CollectionCreateError as e:
            print(f'error ::: {e}')
            return False

    def delete_collection(self, name: str) -> bool:
        try:
            if self.is_collection_existed(name=name):
                self.db.delete_collection(name=name)
                print(f"Collection has deleted: {name}")
            else:
                print(f"Collection already has been deleted: {name}")
            return True
        except CollectionDeleteError as e:
            print(f'error ::: {e}')
            return False

    def insert_documents(self, collections: list[CollectionInformation], overwrite: bool = True):
        def _chunk_list(_data: list, _chunk_size: int = 1000) -> Iterator[list]:
            """
            list[dict] 데이터를 chunk_size 단위로 나누어 Iterator로 반환합니다.

            :param _data: list of dict
            :param _chunk_size: 한 번에 반환할 chunk 크기 (기본값 1000)
            :return: chunk된 list[dict]의 Iterator
            """
            for i in range(0, len(_data), _chunk_size):
                yield _data[i:i+_chunk_size]

        def _insert_documents_once(_name: str, _documents: list[dict], _overwrite: bool) -> None:
            try:
                self.db.collection(name=_name).insert_many(documents=_documents, overwrite=_overwrite)
            except DocumentInsertError as e:
                print(f'error ::: {e}')

        for c in collections:
            name=c.collection
            documents=c.data
            self.create_collection(name=name, is_edge=c.is_edge)
            for doc in _chunk_list(_data=documents):
                _insert_documents_once(_name=name, _documents=doc, _overwrite=overwrite)

    def is_collection_existed(self, name: str) -> bool:
        return self.db.has_collection(name=name)

    def is_view_existed(self, name: str) -> bool:
        try:
            self.db.view(name=name)
            return True
        except ViewGetError as e:
            print(f'error ::: {e}')
            return False

    def is_analyzer_existed(self, name: str) -> bool:
        try:
            self.db.analyzer(name=name)
            return True
        except AnalyzerGetError as e:
            print(f'error ::: {e}')
            return False