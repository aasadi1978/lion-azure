class ExceptionHandler():

    _instance = None
    _data = None

    def __new__(cls):
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._data = ''
            except Exception:
                cls._data = None
        return cls._instance

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        return cls()
    
    def get(self):
        return self._data

    def reset(self):
        self._data = ''

    def update(self, new_data=''):

        if not new_data:
            return
        
        try:
            self._data = f"{self._data}. {new_data}"
        except Exception as e:
            print(f"Failed to update data: {e}")
            self._data = None
    

EXCEPTION_HANDLER = ExceptionHandler.get_instance()