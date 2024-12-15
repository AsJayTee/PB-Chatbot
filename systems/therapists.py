import os
import json
import Levenshtein

class Preferences:
    preferences : dict = dict()

    def get_preferences(self) -> dict:
        return self.preferences

    def update_gender_preferences(self, gender : str) -> None:
        self.preferences["gender"] = [gender]

    def clear_gender_preferences(self) -> None:
        del self.preferences["gender"]
    
    def update_language_preferences(self, language : str) -> None:
        self.preferences["languages"] = [language]
     
    def clear_language_preferences(self) -> None:
        del self.preferences["languages"]

    def update_specialisation_preferences(self, specialisation : str) -> None:
        self.preferences["specialisations"] = [specialisation]
    
    def clear_specialisation_preferences(self) -> None:
        del self.preferences["specialisations"]

    def update_target_age_group_preferences(self, target_age_group : str) -> None:
        self.preferences["target_age_group"] = [target_age_group]
    
    def clear_target_age_group_preferences(self) -> None:
        del self.preferences["target_age_group"]

class Therapists:
    therapist_data : dict
    therapist_map : dict = dict()
    data_folder_path : str = os.environ["DATA_FOLDER_PATH"]

    def __init__(self) -> None:
        self.__load_therapist_data()
        self.__load_therapist_map()

    def get_therapist_data(self) -> dict:
        return self.therapist_data
    
    def get_therapist_map(self) -> dict:
        return self.therapist_map
    
    def get_therapist_factors(self) -> list[str]:
        return list(self.therapist_map.keys())

    def get_therapist_genders(self) -> list[str]:
        gender_map : dict = self.therapist_map.get("gender")
        return list(gender_map.keys())
    
    def get_therapist_languages(self) -> list[str]:
        languages_map : dict = self.therapist_map.get("languages")
        return list(languages_map.keys())

    def get_therapist_specialisations(self) -> list[str]:
        specialisations_map : dict = self.therapist_map.get("specialisations")
        return list(specialisations_map.keys())
    
    def get_therapist_target_age_groups(self) -> list[str]:
        target_age_group_map : dict = self.therapist_map.get("target_age_group")
        return list(target_age_group_map.keys())

    def __load_therapist_data(self) -> dict:
        therapist_data_path = os.path.join(
            self.data_folder_path,
            'therapists.json')
        if os.path.isfile(therapist_data_path):
            with open(therapist_data_path, 'r') as id_map_file:
                therapist_data : dict = json.loads(id_map_file.read())
        else:
            therapist_data = dict()
        self.therapist_data = therapist_data
    
    def __load_therapist_map(self) -> dict:
        for therapist_name, therapist_data in self.therapist_data.items():
            self.__map_gender(therapist_name, therapist_data)
            self.__map_languages(therapist_name, therapist_data)
            self.__map_target_age_group(therapist_name, therapist_data)
            self.__map_specialisations(therapist_name, therapist_data)
            self.__map_availability(therapist_name, therapist_data)
            self.__map_rates(therapist_name, therapist_data)

    def __map_gender(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_gender : str = therapist_data.get("gender")
        gender_map : dict = self.therapist_map.get("gender", dict())
        if not (gender_set := gender_map.get(therapist_gender, set())):
            gender_map[therapist_gender] = gender_set
        gender_set : set
        gender_set.add(therapist_name)
        self.therapist_map["gender"] = gender_map
    
    def __map_languages(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_languages : list[str] = therapist_data.get("languages")
        languages_map : dict = self.therapist_map.get("languages", dict())
        for language in therapist_languages:
            if not (languages_set := languages_map.get(language, set())):
                languages_map[language] = languages_set
            languages_set : set
            languages_set.add(therapist_name)
        self.therapist_map["languages"] = languages_map
    
    def __map_target_age_group(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_target_age_group : dict[str : bool] = therapist_data.get("target_age_group")
        therapist_target_age_group = [k for k, v in therapist_target_age_group.items() if v]
        target_age_group_map : dict = self.therapist_map.get("target_age_group", dict())
        for target_age_group in therapist_target_age_group:
            if not (target_age_group_set := target_age_group_map.get(target_age_group, set())):
                target_age_group_map[target_age_group] = target_age_group_set
            target_age_group_set : set
            target_age_group_set.add(therapist_name)
        self.therapist_map["target_age_group"] = target_age_group_map

    def __map_specialisations(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_specialisations : list[str] = therapist_data.get("specialisations")
        specialisations_map : dict = self.therapist_map.get("specialisations", dict())
        for specialisation in therapist_specialisations:
            if not (specialisations_set := specialisations_map.get(specialisation, set())):
                specialisations_map[specialisation] = specialisations_set
            specialisations_set : set
            specialisations_set.add(therapist_name)
        self.therapist_map["specialisations"] = specialisations_map
    
    def __map_availability(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_availability : dict[str : list] = therapist_data.get("availability")
        therapist_availability = {k : v for k, v in therapist_availability.items() if v is not None}
        availability_map : dict = self.therapist_map.get("availability", dict())
        for day, time_range in therapist_availability.items():
            if not (target_day_map := availability_map.get(day, dict())):
                availability_map[day] = target_day_map
            target_day_map[therapist_name] = time_range
        self.therapist_map["availability"] = availability_map

    def __map_rates(self, therapist_name : str, therapist_data : dict) -> None:
        therapist_rates : dict[str : dict] = therapist_data.get("rates")
        therapist_rates = {k: v for k, v in therapist_rates.items() if any(v.values())}
        rates_map : dict = self.therapist_map.get("rates", dict())
        for rate_type, rate in therapist_rates.items():
            if not (rate_type_map := rates_map.get(rate_type, dict())):
                rates_map[rate_type] = rate_type_map
            rate_type_map[therapist_name] = rate
        self.therapist_map["rates"] = rates_map

class PreferredTherapists:
    therapists : Therapists
    preferences : Preferences = Preferences()

    def __init__(self, therapists : Therapists):
        self.therapists = therapists
    
    def get_preferred_therapists(self) -> list[str]:
        preferred_therapists_set = set(self.therapists.get_therapist_data().keys())
        preferences = self.preferences.get_preferences()
        for key, value in preferences.items():
            refined_therapists = self.therapists.get_therapist_map()
            refined_therapists = refined_therapists[key]
            for nested_key in value:
                refined_therapists = refined_therapists[nested_key]
            preferred_therapists_set = preferred_therapists_set.intersection(refined_therapists)
        return list(preferred_therapists_set)

    def access_therapists(self) -> Therapists:
        return self.therapists
    
    def access_preferences(self) -> Preferences:
        return self.preferences
    
    def update_preferred_gender(self, gender = None) -> None:
        if gender is None:
            self.preferences.clear_gender_preferences()
            return None
        gender_options = self.therapists.get_therapist_genders()
        if gender not in gender_options:
            raise ValueError(
                "'gender' must be one of "
                f"{self.__sort_closest_options(gender, gender_options)}"
                )
        self.preferences.update_gender_preferences(gender)

    def update_preferred_language(self, language = None) -> None:
        if language is None:
            self.preferences.clear_language_preferences()
            return None
        language_options = self.therapists.get_therapist_languages()
        if language not in language_options:
            raise ValueError(
                "'language' must be one of "
                f"{self.__sort_closest_options(language, language_options)}"
                )
        self.preferences.update_language_preferences(language)
    
    def update_preferred_specialisation(self, specialisation = None) -> None:
        if specialisation is None:
            self.preferences.clear_specialisation_preferences()
            return None
        specialisation_options = self.therapists.get_therapist_specialisations()
        if specialisation not in specialisation_options:
            raise ValueError(
                "'specialisation' must be one of "
                f"{self.__sort_closest_options(specialisation, specialisation_options)}"
                )
        self.preferences.update_specialisation_preferences(specialisation)

    def update_preferred_target_age_group(self, target_age_group = None) -> None:
        if target_age_group is None:
            self.preferences.clear_target_age_group_preferences()
            return None
        target_age_group_options = self.therapists.get_therapist_target_age_groups()
        if target_age_group not in target_age_group_options:
            raise ValueError(
                "'target_age_group' must be one of "
                f"{self.__sort_closest_options(target_age_group, target_age_group_options)}"
                )
        self.preferences.update_target_age_group_preferences(target_age_group)

    def __sort_closest_options(self, choice : str, options : list[str]) -> list[str]:
        sorted_options = sorted(options, key = lambda option: Levenshtein.distance(choice, option))
        return sorted_options
