import tiktoken
from typing import Literal

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
