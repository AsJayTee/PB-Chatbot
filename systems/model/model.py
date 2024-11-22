import tiktoken
from openai import OpenAI
from typing import Literal
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.create_embedding_response import CreateEmbeddingResponse

class TokenLimitError(Exception):
    def __init__(self, message = "Token limit exceeded."):
        super().__init__(message)

class PolicyViolationError(Exception):
    def __init__(self, message = "Content violates OpenAI API policies."):
        super().__init__(message)

class UnexpectedError(Exception):
    def __init__(self, message = "An unexpected error occurred."):
        super().__init__(message)

class TokenEncoder:
    chat_encoding : tiktoken.Encoding = tiktoken.get_encoding("o200k_base")
    embed_encoding : tiktoken.Encoding = tiktoken.get_encoding("cl100k_base")

    def get_chat_token_count(text : str) -> int:
        num_tokens = len(TokenEncoder.chat_encoding.encode(text = text))
        return num_tokens
    
    def get_embed_token_count(text : str) -> int:
        num_tokens = len(TokenEncoder.embed_encoding.encode(text = text))
        return num_tokens

class Messages:
    max_messages : int | None
    sys_prompt : dict[str : str]
    convo_messages : list[dict[str : str]]
    convo_tokens : list[int]

    def __init__(self, max_messages : int = None) -> None:
        self.max_messages = max_messages
        self.sys_prompt = {
            "role" : "system",
            "content" : ""
        }
        self.convo_messages = list()
        self.convo_tokens = list()

    def get_max_messages(self) -> int | None:
        return self.max_messages

    def get_sys_prompt(self) -> dict[str : str]:
        return self.sys_prompt

    def get_convo_messages(self) -> list[dict[str : str]]:
        return self.convo_messages
    
    def get_total_tokens(self) -> int:
        sys_prompt_tokens = TokenEncoder.get_chat_token_count(
            self.sys_prompt.get("content")
        )
        return sum(self.convo_tokens) + sys_prompt_tokens
    
    def parse_messages(self) -> list[dict[str : str]]:
        return [self.sys_prompt, *self.convo_messages]
    
    def update_max_messages(self, max_messages : int = None) -> None:
        if max_messages < self.max_messages:
            while len(self.convo_messages) > max_messages:
                self.convo_messages.pop(0)
                self.convo_tokens.pop(0)
        self.max_messages = max_messages
    
    def update_sys_prompt(self, sys_prompt : str) -> None:
        self.sys_prompt["content"] = sys_prompt
    
    def record_message(
            self, 
            content : str, 
            role : Literal["user", "assistant"] = None
            ) -> None:
        self.__check_valid_role(role = role)
        self.__prune_max_messages()
        self.__append_new_message(role = role, content = content)

    def __check_valid_role(self, role : str | None) -> None:
        if role is None:
            raise ValueError(
                f"Invalid input for role: {role} \n" 
                "Must be one of 'user' or 'assistant'.")

    def __prune_max_messages(self) -> None:
        if self.max_messages:
            if len(self.convo_messages) == self.max_messages:
                self.convo_messages.pop(0)
                self.convo_tokens.pop(0)
    
    def __append_new_message(self, role : str, content : str) -> None:
        new_message = {
            "role" : role,
            "content" : content
        }
        token_count = TokenEncoder.get_chat_token_count(content)
        self.convo_messages.append(new_message)
        self.convo_tokens.append(token_count)

class ChatModel:
    client : OpenAI = OpenAI()
    total_prompt_tokens : dict[str : int]
    total_completion_tokens : dict[str : int]

    def __init__(self) -> None:
        self.total_prompt_tokens = {
            "gpt-4o-mini" : 0, "gpt-4o" : 0
        }
        self.total_completion_tokens = {
            "gpt-4o-mini" : 0, "gpt-4o" : 0
        }

    def get_response(
            self,
            messages : Messages,
            model : Literal["gpt-4o-mini", "gpt-4o"] = "gpt-4o-mini"
            ) -> str:
        
        self.__check_token_limit(messages = messages)
        raw_response = self.__call_api(messages = messages, model = model)
        finish_reason = self.__check_finish_reason(raw_response = raw_response)

        if finish_reason == "stop":
            content = self.__handle_stop_response(
                messages = messages,
                model = model,
                raw_response = raw_response
            )
            return content
    
        if finish_reason == "tool_calls":
            pass
    
    def get_cost(self) -> dict[str : float]:
        input_cost_4o = 0.00250 * self.total_prompt_tokens.get("gpt-4o") / 1000
        output_cost_4o = 0.01000 * self.total_completion_tokens.get("gpt-4o") / 1000
        input_cost_4o_mini = 0.000150 * self.total_prompt_tokens.get("gpt-4o-mini") / 1000
        output_cost_4o_mini = 0.000600 * self.total_completion_tokens.get("gpt-4o-mini") / 1000
        return {
            "in-gpt-4o" : round(input_cost_4o, 5),
            "out-gpt-4o" : round(output_cost_4o, 5),
            "in-gpt-4o-mini" : round(input_cost_4o_mini, 6),
            "out-gpt-4o-mini" : round(output_cost_4o_mini , 6)
        }
    
    def __check_token_limit(self, messages : Messages) -> None:
        total_input_tokens = messages.get_total_tokens()
        if total_input_tokens > 128000:
            raise TokenLimitError(
                "Token limit exceeded. \n"
                f"Token limit: 128000 \n"
                f"Tokens passed: {total_input_tokens}"
            )
    
    def __call_api(
            self, 
            messages : Messages,
            model : str
            ) -> ChatCompletion:
        raw_response = self.client.chat.completions.create(
                model = model,
                messages = messages.parse_messages()
            )
        return raw_response
    
    def __check_finish_reason(self, raw_response : ChatCompletion) -> str | None:
        finish_reason = raw_response.choices[0].finish_reason
        if finish_reason == "length":
            raise TokenLimitError
        if finish_reason == "content_filter":
            raise PolicyViolationError
        if finish_reason != "tool_calls" and finish_reason != "stop":
            raise UnexpectedError
        return finish_reason
    
    def __handle_stop_response(
            self,  
            messages : Messages,
            model : str,
            raw_response : ChatCompletion
            ) -> str:
        content = raw_response.choices[0].message.content
        messages.record_message(content = content, role = "assistant")
        self.__record_token_use(raw_response = raw_response, model = model)
        return content

    def __record_token_use(
            self, 
            raw_response : ChatCompletion, 
            model : str
            ) -> None:
        prompt_tokens = raw_response.usage.prompt_tokens
        completion_tokens = raw_response.usage.completion_tokens
        self.total_prompt_tokens[model] += prompt_tokens
        self.total_completion_tokens[model] += completion_tokens

class EmbeddingModel:
    total_tokens : int
    client : OpenAI = OpenAI()

    def __init__(self) -> None:
        self.total_tokens = 0
    
    def generate_embeddings(self, text : str) -> list[float]:
        self.__check_token_limit(text = text)
        raw_response = self.__call_api(text = text)
        embeddings_vector = self.__get_embeddings_vector(raw_response = raw_response)
        self.__record_token_use(raw_response = raw_response)
        return embeddings_vector
    
    def get_cost(self) -> int:
        return self.total_tokens
    
    def __check_token_limit(self, text : str) -> None:
        input_token_size = TokenEncoder.get_embed_token_count(text)
        if input_token_size > 8191:
            raise TokenLimitError(
                token_limit = 8191, 
                token_count = input_token_size)
    
    def __call_api(self, text : str) -> CreateEmbeddingResponse:
        raw_response = self.client.embeddings.create(
            model = "text-embedding-3-small",
            input = text,
            encoding_format = "float"
        )
        return raw_response
    
    def __get_embeddings_vector(self, raw_response : CreateEmbeddingResponse) -> list[float]:
        try:
            embeddings_vector = raw_response.data[0].embedding
        except (AttributeError, IndexError):
            raise UnexpectedError(
                f"Unable to extract output from API response: {raw_response}"
            )
        return embeddings_vector
    
    def __record_token_use(self, raw_response : CreateEmbeddingResponse) -> None:
        self.total_tokens += raw_response.usage.total_tokens

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    newModel = ChatModel()
    messages = Messages()

    system_prompt = input("System prompt: ")
    messages.update_sys_prompt(system_prompt)
    print("Send nothing to end the conversation.")
    user_message = input("Input: ")
    while user_message:
        messages.record_message(user_message, "user")
        print(newModel.get_response(messages))
        user_message = input("Input: ")
    print(newModel.get_cost())
