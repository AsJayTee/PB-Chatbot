from typing import Callable
from systems.therapists import PreferredTherapists
from systems.model.model import Messages, ChatModel

class FilteringAgent:
    messages : Messages
    chat_model : ChatModel
    agent_tools : dict[str : Callable]
    choose_category_message : Messages
    preferred_therapists : PreferredTherapists

    def __init__(
            self,
            messages : Messages,
            chat_model : ChatModel,
            preferred_therapists : PreferredTherapists
            ) -> None:
        self.messages = messages
        self.chat_model = chat_model
        self.preferred_therapists = preferred_therapists
        self.choose_category_message = Messages(max_messages = 1)
        categories = preferred_therapists.access_therapists().get_therapist_factors()
        self.choose_category_message.update_sys_prompt(
            self.choose_category_prompt.format(categories = categories))
        self.agent_tools = {
            "None" : self.__handle_mismatch_category,
            "gender" : self.__filter_gender,
            "languages" : self.__filter_languages,
            "target_age_group" : self.__filter_target_age_group,
            "specialisations" : self.__filter_specialisations
        }
    
    def main(self, **kwargs) -> str:
        ori_sys_prompt = self.messages.get_sys_prompt()
        self.messages.update_sys_prompt(sys_prompt = self.rephrase_preference_prompt)
        rephrased_preference = self.chat_model.get_response(
            messages = self.messages,
            model = "gpt-4o-mini",
            record_response = False
        )
        self.choose_category_message.record_message(
            content = rephrased_preference,
            role = 'user'
        )
        print(self.choose_category_message.parse_messages())
        category = self.chat_model.get_response(
            messages = self.choose_category_message,
            model = "gpt-4o-mini",
            record_response = False
        )
        print(category)
        result = self.agent_tools.get(category)(rephrased_preference)
        self.messages.update_sys_prompt(sys_prompt = ori_sys_prompt)
        if result is None:
            return str(self.preferred_therapists.get_preferred_therapists())
        return result

    rephrase_preference_prompt : str = \
    "Given a chat history and the latest user preference " \
    "which might reference context in the chat history, " \
    "formulate a standalone preference which can " \
    "be understood without the chat history. " \
    "Do NOT modify the latest preference, just reformulate it " \
    "if needed and otherwise return it as is. Be concise." 

    choose_category_prompt : str = \
    "Given a user preference, choose the category this preference falls under. " \
    "Available categories: {categories}. " \
    "Respond with the category only and say nothing else. " \
    "If none of the categories match, reply with None and say nothing else."

    def __handle_mismatch_category(self, rephrased_preference : str) -> str:
        pass

    def __filter_gender(self, rephrased_preference : str) -> None | str:
        pass

    def __filter_languages(self, rephrased_preference : str) -> None | str:
        pass

    def __filter_target_age_group(self, rephrased_preference : str) -> None | str:
        pass

    def __filter_specialisations(self, rephrased_preference : str) -> None | str:
        pass
