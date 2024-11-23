import os
import json
from model.model import EmbeddingModel
from faiss import IndexFlatIP, IndexIDMap, read_index

class VectorstoreManager:
    counter : int
    vectorstore : IndexIDMap
    embedding_model : EmbeddingModel
    id_map : dict[int : tuple[str, str]] | None
    data_folder_path : str = os.environ["DATA_FOLDER_PATH"]
    
    def __init__(self, embedding_model : EmbeddingModel) -> None:
        self.__load_id_map()
        self.__load_vectorstore()
        self.embedding_model = embedding_model

    def __load_id_map(self) -> dict[int : tuple[str, str]]:
        id_map_path = os.path.join(
            self.data_folder_path,
            'id_map.json')
        if os.path.isfile(id_map_path):
            with open(id_map_path, 'r') as id_map_file:
                id_map : dict = json.loads(id_map_file.read())
                self.counter = id_map.pop("__counter")
        else:
            id_map = dict()
            self.counter = 0
        self.id_map = id_map

    def __load_vectorstore(self) -> IndexIDMap:
        vectorstore_path = os.path.join(
            self.data_folder_path,
            'vectorstore.index'
        )
        if os.path.isfile(vectorstore_path):
            self.vectorstore = read_index(vectorstore_path)
        else:
            temp_index = IndexFlatIP(1536)
            self.vectorstore = IndexIDMap(temp_index)
