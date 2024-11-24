import json
from systems.vectorstore import VectorstoreManager
from systems.model.model import Messages, ChatModel

class RAG:
    messages : Messages
    chat_model : ChatModel
    vectorstore_manager : VectorstoreManager

    def __init__(
            self, 
            messages : Messages,
            chat_model : ChatModel, 
            vectorstore_manager : VectorstoreManager
            ) -> None:
        self.messages = messages
        self.chat_model = chat_model
        self.vectorstore_manager = vectorstore_manager
    
    def main(self, **kwargs) -> str:
        ori_sys_prompt = self.messages.get_sys_prompt()
        self.messages.update_sys_prompt(sys_prompt = self.rephrase_question_prompt)
        rephrased_question = self.chat_model.get_response(
            messages = self.messages,
            model = "gpt-4o-mini",
            record_response = False
        )
        context = self.vectorstore_manager.get_context(query = rephrased_question)
        self.messages.update_sys_prompt(sys_prompt = ori_sys_prompt)
        return json.dumps(context)

    rephrase_question_prompt : str = \
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can "
    "be understood without the chat history. "
    "Do NOT answer the question, just reformulate it "
    "if needed and otherwise return it as is. Be concise."
