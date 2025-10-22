
from dataclasses import dataclass
from lion.utils.singleton_meta import SingletonMeta


@dataclass
class StatusBarManager(metaclass=SingletonMeta):

    _instance=None

    STATUS_VALUE: float = 0.0
    PROGRESS_PERCENTAGE_STR: str = '0%'
    PROGRESS_INFO: str = ''
    POPUP_MESSAGE: str = ''

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance.PROGRESS_PERCENTAGE_STR = '0%'
            cls._instance.PROGRESS_INFO = ''
            cls._instance.POPUP_MESSAGE = ''
            cls._instance.STATUS_VALUE = 0.0
        
        return cls._instance
    
    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        return cls()

    def clear_info(self):
        self.PROGRESS_INFO = ''

    def reset(self):

        self.PROGRESS_PERCENTAGE_STR = '0%'
        self.PROGRESS_INFO = ''
        self.POPUP_MESSAGE = ''
        self.STATUS_VALUE = 0.0
    
    def update_status_progress(self, current_x=0, maxVal=100):
        try:
            valFrac = current_x/maxVal
            self.STATUS_VALUE = min(valFrac, 0.99) * 100 if current_x < maxVal else current_x * 100/maxVal
            self.PROGRESS_PERCENTAGE_STR = f"{min(valFrac, 0.99) * 100 if current_x < maxVal else current_x * 100/maxVal:.2f}%"

            if not current_x:
                self.PROGRESS_PERCENTAGE_STR = '0%'
                self.PROGRESS_INFO = ''
                self.STATUS_VALUE = 0.0

        except Exception as err :
            self.PROGRESS_INFO = f'Error in update_status_progress: {str(err)}'
            self.PROGRESS_PERCENTAGE_STR = '0%'
            self.STATUS_VALUE = 0.0

STATUS_CONTROLLER = StatusBarManager.get_instance()