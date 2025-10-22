from flask import url_for
from lion.utils.map_pushpin import pushpin

class PushpinData():

    _instance = None
    _data = None

    def __new__(cls):
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._data = cls.load_dct_pushpins()
            except Exception:
                cls._data = None
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()
    
    @classmethod
    def load_dct_pushpins(cls):

        try:
            dct_pushpins = pushpin()
            set_types = set(dct_pushpins)

            for loctype in set_types:
                dct_pushpins[loctype]['path'] = url_for(
                    'static', filename=f"images/{dct_pushpins[loctype]['imageFile']}")
        except Exception as e:
            dct_pushpins = {}
        
        return dct_pushpins

    def get(self):
        return self._data

PUSHPIN_DATA = PushpinData.get_instance()