from googletrans import Translator
from lion.create_flask_app.create_app import LION_FLASK_APP

# We can replace this engine later with something else (e.g., DeepL API, Azure Translator, OpenAI API, etc).
class TranslatorEngine:
    def __init__(self):
        self._translator = Translator()

    def translate(self, text, src='en'):
        return self._translator.translate(text, src=src, dest=LION_FLASK_APP.config['LION_REGION_LANGUAGE']).text
