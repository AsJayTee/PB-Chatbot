import os
import json
import shutil
import numpy as np
from model.model import EmbeddingModel
from faiss import IndexFlatIP, IndexIDMap, read_index, write_index

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

    def update_vectorstore(self) -> None:
        faq_data = self.__load_faq_data()
        if not faq_data:
            self.__reset_vectorstore()
            self.__save_state()
            return None
        new_faq_questions = set(faq_data.keys())
        self.__handle_disjoint_questions(
            new_faq_questions = new_faq_questions,
            faq_data = faq_data
            )
        self.__save_state()

    def reset_all(self) -> None:
        for root, dirs, files in os.walk(self.data_folder_path):
            for file in files:
                os.unlink(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))
        self.update_vectorstore()

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
    
    def __load_faq_data(self) -> dict[str : str] | None:
        faq_path = os.path.join(
            self.data_folder_path,
            'FAQs.json')
        if os.path.isfile(faq_path):
            with open(faq_path, 'r') as faqs_file:
                return json.loads(faqs_file.read())
    
    def __reset_vectorstore(self) -> None:
        self.counter = 0
        self.vectorstore = IndexIDMap(IndexFlatIP(1536))
        self.id_map = dict()

    def __handle_disjoint_questions(self, new_faq_questions : set, faq_data : dict) -> None:
        self.__delete_old_questions(new_faq_questions = new_faq_questions, faq_data = faq_data)
        self.__add_new_questions(new_faq_questions = new_faq_questions, faq_data = faq_data)

    def __delete_old_questions(self, new_faq_questions : set, faq_data : dict) -> set:
        ids_to_remove = list()
        for key, value in self.id_map.items():
            try:
                new_faq_questions.remove(value[0])
                self.id_map[key] = (value[0], faq_data.get(value[0]))
            except KeyError:
                id = np.array([key], dtype = 'int64')
                self.vectorstore.remove_ids(id)
                ids_to_remove.append(key)
        for key in ids_to_remove:
            self.id_map.pop(key)
        return new_faq_questions
    
    def __add_new_questions(self, new_faq_questions : set, faq_data : dict) -> None:
        for question in new_faq_questions:
            self.id_map[self.counter] = (question, faq_data.get(question))
            vector = self.embedding_model.generate_embeddings(text = question)
            vector = np.array(vector).reshape(1, -1)
            self.vectorstore.add_with_ids(vector, self.counter)
            self.counter += 1

    def __save_state(self) -> None:
        self.__save_vectorstore()
        self.__save_id_map()
        
    def __save_vectorstore(self) -> None:
        vectorstore_path = os.path.join(
            self.data_folder_path,
            'vectorstore.index')
        write_index(self.vectorstore, vectorstore_path)
    
    def __save_id_map(self) -> None:
        id_map_path = os.path.join(
            self.data_folder_path,
            'id_map.json'
        )
        self.id_map["__counter"] = self.counter
        with open(id_map_path, 'w') as id_map_file:
            json.dump(
                self.id_map,
                id_map_file,
                indent = 4
            )

if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()
    embed_model = EmbeddingModel()
    vm = VectorstoreManager(embed_model)
    vm.update_vectorstore()
    print(embed_model.get_cost())