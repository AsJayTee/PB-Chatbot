import os
import json
import logging
import tiktoken
from openai import OpenAI
from typing import Literal, Callable
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

    def __repr__(self) -> str:
        return str(self.parse_messages())

    def get_max_messages(self) -> int | None:
        return self.max_messages

    def get_sys_prompt(self) -> str:
        return self.sys_prompt.get("content")

    def get_convo_messages(self) -> list[dict[str : str]]:
        return self.convo_messages
    
    def get_latest_convo_message(self) -> str:
        return self.get_convo_messages()[-1].get("content")
    
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

    def record_tool_call(
            self,
            tool_call_id : str,
            tool_call_args_json : str,
            tool_call_name : str
            ) -> None:
        self.__prune_max_messages()
        self.__append_new_tool_call(
            tool_call_id = tool_call_id,
            tool_call_args_json = tool_call_args_json,
            tool_call_name = tool_call_name
        )
    
    def record_tool_response(
            self,
            tool_call_id : str,
            tool_response_json : str
            ) -> None:
        self.__prune_max_messages()
        self.__append_new_tool_response(
            tool_response_json = tool_response_json,
            tool_call_id = tool_call_id
        )

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
    
    def __append_new_tool_call(
            self,
            tool_call_id : str,
            tool_call_args_json : str,
            tool_call_name : str
            ) -> None:
        new_message = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "arguments": tool_call_args_json,
                        "name": tool_call_name
                    }
                }
            ]
        }
        token_count = TokenEncoder.get_chat_token_count(json.dumps(new_message))
        self.convo_messages.append(new_message)
        self.convo_tokens.append(token_count)
    
    def __append_new_tool_response(
            self,
            tool_response_json : str,
            tool_call_id : str
            ) -> None:
        new_message = {
            "role": "tool",
            "content": tool_response_json,
            "tool_call_id": tool_call_id
        }
        token_count = TokenEncoder.get_chat_token_count(json.dumps(new_message))
        self.convo_messages.append(new_message)
        self.convo_tokens.append(token_count)

class Tools:
    tools_list : list[dict]
    tools_dict : dict[str : Callable]

    def __init__(self):
        self.tools_list = list()
        self.tools_dict = dict()

    def get_tools(self) -> list[dict]:
        return self.tools_list
    
    def add_tool(
        self,
        func : Callable,
        func_name : str,
        func_desc : str,
        arg_names : list[str] = None,
        arg_descs : list[str] = None,
        required_args : list[str] | str = "all"
        ) -> None:

        if arg_names is None:
            arg_names = []
        if arg_descs is None:
            arg_descs = []
        if required_args == "all":
            required_args = arg_names

        self.__args_num_check(
            arg_names = arg_names,
            arg_descs = arg_descs
        )

        arg_types = ["string"] * len(arg_names)
        
        func_properties = self.__get_func_properties(
            arg_names = arg_names, 
            arg_types = arg_types, 
            arg_descs = arg_descs
        )
        
        json_format_function = self.__get_json_format_function(
            func_name = func_name,
            func_desc = func_desc,
            func_properties = func_properties,
            required_args = required_args
        )

        tool = {
            "type" : "function",
            "function" : json_format_function
        }
        self.tools_list.append(tool)
        self.tools_dict[func_name] = func

    def remove_tool(self, function_name : str) -> None:
        self.tools_list = list(
            filter(
                lambda x : x["function"]["name"] != \
                    function_name, 
                self.tools_list
            )
        )
    
    def use_tool(self, func_name : str, func_args_json : str):
        func_args = json.loads(func_args_json)
        return self.tools_dict.get(func_name)(**func_args)

    def __args_num_check(
            self, 
            arg_names : list[str], 
            arg_descs : list[str]
            ) -> None:
        if len(arg_names) != len(arg_descs):
            raise ValueError(
                "No. of arguments and descriptions are not consistent. "
                f"No. of arguments: {len(arg_names)}, "
                f"No. of descriptions: {len(arg_descs)}"
            )

    def __get_func_properties(
        self, 
        arg_names : list[str], 
        arg_types : list[str], 
        arg_descs : list[str]
        ) -> dict[str : dict]:
        func_properties = dict()
        for indiv_arg_name, indiv_arg_type, indiv_arg_desc in \
        zip(arg_names, arg_types, arg_descs):
            func_properties[indiv_arg_name] = {
                "type" : indiv_arg_type,
                "description" : indiv_arg_desc
            }
        return func_properties

    def __get_json_format_function(
        self,
        func_name : str,
        func_desc : str,
        func_properties : dict,
        required_args : list[str]
        ):
        return {
            "name" : func_name,
            "description" : func_desc,
            "parameters" : {
                "type" : "object",
                "properties" : func_properties
            },
            "required" : required_args,
            "additionalProperties" : False
        }

class ChatModel:
    debug : bool = False
    client : OpenAI = OpenAI()
    logger = logging.getLogger(__name__)
    total_prompt_tokens : dict[str : int]
    total_completion_tokens : dict[str : int]
    logs_folder_path : str = os.environ["LOGS_FOLDER_PATH"]

    def __init__(self) -> None:
        self.total_prompt_tokens = {
            "gpt-4o-mini" : 0, "gpt-4o" : 0
        }
        self.total_completion_tokens = {
            "gpt-4o-mini" : 0, "gpt-4o" : 0
        }
        logging.basicConfig(
            level = logging.INFO,
            format = '%(asctime)s - %(levelname)s - %(message)s',
            handlers = [
                logging.FileHandler(
                    os.path.join(self.logs_folder_path, "model.log")
                    )
                ]
            )

    def get_response(
            self,
            messages : Messages,
            tools : Tools = None,
            model : Literal["gpt-4o-mini", "gpt-4o"] = "gpt-4o-mini",
            record_response : bool = True
            ) -> str:
        
        self.__check_token_limit(messages = messages)
        raw_response = self.__call_api(messages = messages, tools = tools, model = model)
        finish_reason = self.__check_finish_reason(raw_response = raw_response)

        if self.debug:
            self.logger.debug(messages.get_latest_convo_message())
        else:
            self.logger.info(messages.get_latest_convo_message())

        if finish_reason == "stop":
            content = self.__handle_stop_response(
                messages = messages,
                model = model,
                raw_response = raw_response,
                record_response = record_response
            )
            if self.debug:
                self.logger.debug(content)
                self.logger.debug(messages)
            else:
                self.logger.info(content)
                self.logger.info(messages)
            return content
    
        if finish_reason == "tool_calls":
            self.__handle_tool_calls_response(
                messages = messages,
                model = model,
                raw_response = raw_response,
                tools = tools
            )
            return self.get_response(
                messages = messages,
                tools = tools,
                model = model
            )
    
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
    
    def enable_debug(self) -> None:
        self.debug = True
        logging.basicConfig(
            level = logging.DEBUG,
            format = '%(asctime)s - %(levelname)s - %(message)s',
            handlers = [logging.StreamHandler()]
            )
    
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
            tools : Tools | None,
            model : str
            ) -> ChatCompletion:
        raw_response = self.client.chat.completions.create(
                model = model,
                messages = messages.parse_messages(),
                tools = None if tools is None else tools.get_tools()
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
            raw_response : ChatCompletion,
            record_response : bool
            ) -> str:
        content = raw_response.choices[0].message.content
        if record_response:
            messages.record_message(content = content, role = "assistant")
        self.__record_token_use(raw_response = raw_response, model = model)
        return content
    
    def __handle_tool_calls_response(
            self,
            messages : Messages,
            model : str,
            raw_response : ChatCompletion,
            tools : Tools
            ) -> None:
        tool_call_id = raw_response.choices[0].message.tool_calls[0].id
        tool_call_name = raw_response.choices[0].message.tool_calls[0].function.name
        tool_call_args_json = raw_response.choices[0].message.tool_calls[0].function.arguments
        tool_response_json = tools.use_tool(
            func_name = tool_call_name,
            func_args_json = tool_call_args_json
        )
        messages.record_tool_call(
            tool_call_id = tool_call_id,
            tool_call_args_json = tool_call_args_json,
            tool_call_name = tool_call_name
        )
        messages.record_tool_response(
            tool_call_id = tool_call_id,
            tool_response_json = tool_response_json
        )
        self.__record_token_use(raw_response = raw_response, model = model)

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
    
    def get_cost(self) -> float:
        embed_cost = 0.000020 * self.total_tokens / 1000
        return round(embed_cost, 6)
    
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
