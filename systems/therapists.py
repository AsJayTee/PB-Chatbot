import os
import json

class Preferences:
    pass

class Therapists:
    therapist_data : dict
    therapist_map : dict = dict()
    preferences : Preferences
    data_folder_path : str = os.environ["DATA_FOLDER_PATH"]

    def __init__(self, preferences : Preferences) -> None:
        self.__load_therapist_data()
        self.__load_therapist_map()
        self.preferences = preferences
    
    def get_therapists(self) -> list[str]:
        pass

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

from pprint import pprint
tr = Therapists()
pprint(tr.therapist_map)
