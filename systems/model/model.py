import tiktoken

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