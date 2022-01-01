import os
import json
from bot.utils.generics import get_config


class Translator:
    def __init__(self):
        self.translation_data = self._get_translation_data()

    @staticmethod
    def _get_translation_data():
        translation_data = dict()

        for file_name in os.listdir('languages'):
            language = file_name[:-5]
            with open("languages/{}".format(file_name)) as file:
                translation_data[language] = json.load(file)

        return translation_data

    def message(self, guild_id, function, message):
        guild = get_config(guild_id)
        guild_language = guild["language"]
        try:
            return self.translation_data[guild_language][function][message]
        except KeyError:
            return self.translation_data["english"][function][message]
