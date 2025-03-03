from typing import Callable
from systems.therapists import PreferredTherapists
from systems.model.model import Messages, ChatModel, Tools

class FilteringAgent:
    messages : Messages
    chat_model : ChatModel
    agent_tools : dict[str : Callable]
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
        self.agent_tools = {
            "None" : self.__handle_mismatch_category,
            "gender" : self.__filter_gender,
            "languages" : self.__filter_languages,
            "patient_age_group" : self.__filter_patient_age_group,
            "specialisations" : self.__filter_specialisations,
            "rates" : self.__filter_price
        }
    
    def main(self, **kwargs) -> str:
        ori_sys_prompt = self.messages.get_sys_prompt()
        categories = self.preferred_therapists.access_therapists().get_therapist_factors()
        self.messages.update_sys_prompt(sys_prompt = self.rephrase_preference_prompt)
        rephrased_preference = self.chat_model.get_response(
            messages = self.messages,
            model = "gpt-4o-mini",
            record_response = False
        )
        self.messages.update_sys_prompt(
            sys_prompt = self.choose_category_prompt.format(categories = categories))
        category = self.chat_model.get_response(
            messages = self.messages,
            model = "gpt-4o-mini",
            record_response = False
        )
        selected_tool = self.agent_tools.get(category, None)
        if selected_tool is None:
            return "An error has ocurred. Please call the tool again."
        result = selected_tool(rephrased_preference)
        self.messages.update_sys_prompt(sys_prompt = ori_sys_prompt)
        if result is None:
            return str(self.preferred_therapists.get_preferred_therapists())
        return result

    def get_therapist_info(self, **kwargs) -> str:
        ori_sys_prompt = self.messages.get_sys_prompt()
        self.messages.update_sys_prompt(sys_prompt = self.get_therapist_name_prompt)
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.get_therapist_info,
            "get_therapist_info",
            "Get therapist info based on their name. " \
            "If there is no match, it will fetch information from the closest name.",
            ["therapist_name"],
            ["Therapist name."]
        )
        response = self.chat_model.get_response(
            messages = self.messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        self.messages.update_sys_prompt(sys_prompt = ori_sys_prompt)
        return response

    rephrase_preference_prompt : str = \
    "Given a chat history and the latest user preference " \
    "which might reference context in the chat history, " \
    "formulate a standalone preference which can " \
    "be understood without the chat history. " \
    "Do NOT modify the latest preference, just reformulate it " \
    "if needed and otherwise return it as is. Be concise. " \
    "If the user preference relates to their own age, use the term " \
    "'patient age group' to describe their preference."

    get_therapist_name_prompt : str = \
    "Given the names of therapists, use the tools available to you to " \
    "get their information and return it."

    choose_category_prompt : str = \
    "Given a chat history, choose the category the latest user preference falls under. " \
    "Available categories: {categories}. " \
    "Respond with the category only and say nothing else. " \
    "If none of the categories match, reply with None and say nothing else."
    "If the provided preference references previous preferences, "
    "focus on choosing the category based on newer information."
    "You MUST say nothing else and answer with only the category name, or None."

    handle_mismatch_response : str = \
    "The user preference provided was not able to be used in the system. " \
    "Relay this information kindly to the user and suggest a factor that they can consider. " \
    "Provided preference: {preference}. " \
    "Available factors in system: {factors}. " \
    "Do NOT repeat all the available factors. " \
    "Instead, ask a question to help them consider one of the available factors."

    filter_gender_prompt : str = \
    "Using the user preference provided, update their preferred therapist's gender. " \
    "Call the tool provided until you have either successfully updated their preference, " \
    "or know that their preference is not one of the possible options. " \
    "Possible options: {possible_genders}. " \
    "If you are able to update their preference, reply with Done. " \
    "If you are not able to update their preference, reply with Error."

    filter_languages_prompt : str = \
    "Using the user preference provided, update the preferred language their therapist speaks. " \
    "Call the tool provided until you have either successfully updated their preference, " \
    "or know that their preference is not one of the possible options. " \
    "Possible options: {possible_languages}. " \
    "If you are able to update their preference, reply with Done. " \
    "If you are not able to update their preference, reply with Error."

    filter_patient_age_group_prompt : str = \
    "Using the user preference provided, update their preferred therapist's target patient age group. " \
    "Call the tool provided until you have either successfully updated their preference, " \
    "or know that their preference is not one of the possible options. " \
    "Possible options: {possible_patient_age_groups}. " \
    "If you are able to update their preference, reply with Done. " \
    "If you are not able to update their preference, reply with Error."

    filter_specialisations_prompt : str = \
    "Using the user information provided, update their most suitable therapist's specialisation. " \
    "Call the tool provided until you have either successfully updated their preference, " \
    "or know that their preference is not one of the possible options. " \
    "Possible options: {possible_specialisations}. " \
    "If you are able to update their preference, reply with Done. " \
    "If you are not able to update their preference, reply with Error."

    filter_price_prompt : str = \
    "Using the user preference provided, update their preferred therapist's price. " \
    "Call the tool provided until you have either successfully updated their preference, " \
    "or know that it is not possible to accomodate their preference. " \
    "If you are able to update their preference, reply with Done. " \
    "If you are not able to update their preference, reply with Error and explain what went wrong."

    def __handle_mismatch_category(self, preference : str) -> str:
        factors = self.preferred_therapists.access_therapists().get_therapist_factors()
        return self.handle_mismatch_response.format(preference = preference, factors = factors)

    def __filter_gender(self, preference : str) -> None | str:
        possible_genders = self.preferred_therapists.access_therapists().get_therapist_genders()
        messages = Messages()
        messages.update_sys_prompt(
            self.filter_gender_prompt.format(possible_genders = possible_genders)
        )
        messages.record_message(
            content = preference,
            role = 'user'
        )
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.update_preferred_gender,
            "update_preferred_gender",
            "Records the user's preferred therapist gender in the system.",
            ["gender"],
            ["Preferred therapist gender."]
        )
        response = self.chat_model.get_response(
            messages = messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        if response.startswith("Done"):
            return None
        elif response.startswith("Error"):
            return \
            "Inform the user that there are no therapists with their preferred gender at the moment. " \
            "Be kind and suggest they choose one of the possible genders. " \
            f"Available therapist genders: {possible_genders}."
        else:
            return response

    def __filter_languages(self, preference : str) -> None | str:
        possible_languages = self.preferred_therapists.access_therapists().get_therapist_languages()
        messages = Messages()
        messages.update_sys_prompt(
            self.filter_languages_prompt.format(possible_languages = possible_languages)
        )
        messages.record_message(
            content = preference,
            role = 'user'
        )
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.update_preferred_language,
            "update_preferred_language",
            "Records the user's preferred language in the system.",
            ["language"],
            ["Preferred language the therapist speaks."]
        )
        response = self.chat_model.get_response(
            messages = messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        if response.startswith("Done"):
            return None
        elif response.startswith("Error"):
            return \
            "Inform the user that there are no therapists who speak their preferred language at the moment. " \
            "Be kind and suggest they choose one of the possible languages. " \
            f"Available therapist languages: {possible_languages}." 
        else:
            return response

    def __filter_patient_age_group(self, preference : str) -> None | str:
        possible_patient_age_groups = self.preferred_therapists.access_therapists().get_therapist_patient_age_groups()
        messages = Messages()
        messages.update_sys_prompt(
            self.filter_patient_age_group_prompt.format(possible_patient_age_groups = possible_patient_age_groups)
        )
        messages.record_message(
            content = preference,
            role = 'user'
        )
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.update_preferred_patient_age_group,
            "update_preferred_patient_age_group",
            "Records the user's preferred therapist's target patient age group in the system.",
            ["patient_age_group"],
            ["Therapist's target patient age group."]
        )
        response = self.chat_model.get_response(
            messages = messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        if response.startswith("Done"):
            return None
        elif response.startswith("Error"):
            return \
            "Inform the user that there are no therapists with their preferred target patient age group at the moment. " \
            "Be kind and suggest they choose one of the possible target patient age groups. " \
            f"Available therapist's target patient age groups: {possible_patient_age_groups}." 
        else:
            return response

    def __filter_specialisations(self, preference : str) -> None | str:
        possible_specialisations = self.preferred_therapists.access_therapists().get_therapist_specialisations()
        messages = Messages()
        messages.update_sys_prompt(
            self.filter_specialisations_prompt.format(possible_specialisations = possible_specialisations)
        )
        messages.record_message(
            content = preference,
            role = 'user'
        )
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.update_preferred_specialisation,
            "update_preferred_specialisation",
            "Records the user's most suitable therapist specialisation in the system.",
            ["specialisation"],
            ["Therapist's specialisation."]
        )
        response = self.chat_model.get_response(
            messages = messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        if response.startswith("Done"):
            return None
        elif response.startswith("Error"):
            return \
            "Inform the user that there are no therapists with their preferred specialisation at the moment. " \
            "Be kind and suggest they choose one of the possible specialisations. " \
            f"Available therapist specialisations: {possible_specialisations}." 
        else:
            return response

    def __filter_price(self, preference : str) -> None | str:
        messages = Messages()
        messages.update_sys_prompt(self.filter_price_prompt)
        messages.record_message(
            content = preference, 
            role = 'user'
        )
        tools = Tools()
        tools.add_tool(
            self.preferred_therapists.update_preferred_price,
            "update_preferred_price", 
            "Records the user's preferred therapist price range in the system.",
            ["upper_bound", "lower_bound", "type"],
            [
                "Price upper bound. Must be an integer.", 
                "Price lower bound. Must be an integer.", 
                "Type of therapy. Can only be one of ['individual', 'couples', 'family']"
            ],
            ["type"]
        )
        response = self.chat_model.get_response(
            messages = messages,
            tools = tools,
            model = "gpt-4o-mini"
        )
        print(response)
        if response.startswith("Done"):
            return None
        else:
            return response
