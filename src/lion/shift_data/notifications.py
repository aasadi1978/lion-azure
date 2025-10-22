class NotificationHandler():

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
        try:
            self._data = ''
        except Exception:
            self._data = None

    def update(self, new_data=''):

        if not new_data:
            return
        
        try:
            self._data = f"{self._data}. {new_data}"
        except Exception as e:
            print(f"Failed to update data: {e}")
            self._data = None

NOTIFICATION_HANDLER = NotificationHandler.get_instance()