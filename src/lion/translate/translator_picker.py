from lion.translate.french_wrapper import FrenchTranslatorWrapper
from lion.translate.german_wrapper import GermanTranslatorWrapper
from lion.translate.italian_wrapper import ItalianTranslatorWrapper
from lion.translate.spanish_wrapper import SpanishTranslatorWrapper
from lion.translate.trans_engine import TranslatorEngine
from lion.create_flask_app.create_app import LION_FLASK_APP

class TranslatorPicker:

    def __init__(self):
        pass
    
    @classmethod
    def translator(cls):
        """Return the appropriate translator based on the current language setting."""
        if LION_FLASK_APP.config['LION_REGION_LANGUAGE'] == 'FR':
            return FrenchTranslatorWrapper(engine=TranslatorEngine())

        if LION_FLASK_APP.config['LION_REGION_LANGUAGE'] == 'ES':
            return SpanishTranslatorWrapper(engine=TranslatorEngine())

        if LION_FLASK_APP.config['LION_REGION_LANGUAGE'] == 'IT':
            return ItalianTranslatorWrapper(engine=TranslatorEngine())

        if LION_FLASK_APP.config['LION_REGION_LANGUAGE'] == 'DE':
            return GermanTranslatorWrapper(engine=TranslatorEngine())
        
        return None


TRANSLATOR = TranslatorPicker.translator()