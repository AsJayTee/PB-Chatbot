from vectorstore import VectorstoreManager
from model.model import Messages, ChatModel

class RAG:
    messages : Messages
    chat_model : ChatModel
    vectorstore_manager : VectorstoreManager

    def __init__(self) -> None:
        pass
