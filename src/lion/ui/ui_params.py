from dataclasses import MISSING, dataclass, field
from typing import Dict, List, Set

from lion.logger.exception_logger import log_exception
from lion.utils.singleton_meta import SingletonMeta



@dataclass
class UIParams(metaclass=SingletonMeta):

    _instance = None

    CHANGEOVERS_VALIDATED: bool = False
    LION_REGION: str = 'GB'
    LIST_FILTERED_SHIFT_IDS: List[str] = field(default_factory=list)
    LIST_SELECTED_CHANGEOVERS: List[str] = field(default_factory=list)
    DICT_DRIVERS_PER_PAGE: Dict= field(default_factory=dict)
    SET_IMPACTED_SHIFTS: Set[int]= field(default_factory=lambda: set())
    ALL_WEEK_DRIVERS_FILTERED: List[str]= field(default_factory=list)
    FILTERING_VEHICLES: List[str]= field(default_factory=list)
    DCT_FILTER_PARAMS: Dict= field(default_factory=dict)
    PAGE_NUM: int= 1
    PAGE_SIZE: int= 15
    RETURN_FULL_PLAN: bool= False
    FILTERING_LOC_CODES: List[str]= field(default_factory=list)
    DCT_TRAFFIC_TYPE_COLORS: Dict  = field(default_factory=dict)
    DCT_CACHED_INFO: Dict= field(default_factory=dict)
    FILTERING_WKDAYS: List[str]= field(default_factory=list)
    BAR_WIDTH: str = '45;40;35'
    UTILISATION_RANGE: List[int]= field(default_factory=lambda: [0, 100])
    HIDE_FIXED: bool = False
    HIDE_INFEASIBLE: bool = False
    HIDE_BLANK: bool = False
    RIGHT_CLICK_ID: int = 0
    MEMORY_USAGE: int = 0
    OPTIONS: Dict = field(default_factory=dict)
    REQUEST_BLOCKER: bool = False
    ENABLE_LOGGING: bool = False
    FULL_WEEK_CLICKED: bool = False
    LOAD_BASKET_FLAG: bool = False
    SHIFT_INFO: str = ''
    SORT_BY_TOUR_LOCSTRING: bool = False
    
    # UPDATE_SUPPLIERS is a flag to indicate if suppliers need to be updated. When user has a list of shiftnames after tender process 
    # with attached suppliers. Used in driveres_info.update_suppliers
    UPDATE_SUPPLIERS: bool = False 
    LOCATION_COLLOCATION_THRESHOLD: float = 0.0001 # This is a threshold for determining if two locations are colocated based on their coordinates.

    MAXIMUM_DOWNTIME: int = 360
    DOUBLE_MAN_SHIFT_DUR: int = 990
    LIST_BREAK_MIN: List[int] = field(default_factory=lambda: [0, 30, 60])
    DRIVING_TIME_B4_BREAK: int = 270
    MIN_BREAK_TIME_WORKING: int = 30
    WORKING_TIME_B4_BREAK: int = 360
    MIN_BREAK_TIME: int = 60
    MAX_REPOS_DRIV_MIN: int = 270
    MAX_TOUR_DUR: int = 720
    MAX_DRIVING_DUR: int = 540

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.initialize()

    def initialize(self):

        try:
            for field_name, field_def in self.__dataclass_fields__.items():
                if field_def.default_factory is not MISSING:
                    setattr(self, str(field_name).upper(), field_def.default_factory())
                elif field_def.default is not MISSING:
                    setattr(self, str(field_name).upper(), field_def.default)
                else:
                    setattr(self, str(field_name).upper(), None)
                
                self._initialized = True
                
        except Exception as e:
            log_exception(f"Error initializing UIParams: {e}")

            self._initialized = False

    def is_new_lion_version(self) -> bool:
        try:
            return str(self.CURRENT_VERSION).replace("lion-", "") != str(self.SRC_WHL_VERSION).replace("lion-", "")
        except Exception:
            log_exception(False)
            return False
        
    @classmethod
    def get_instance(cls):
        return cls()

    def get(self, param: str = '', if_null=None):
        try:
            return getattr(self, param.upper(), if_null)
        except Exception:
            log_exception(False)
            return if_null

    def pop(self, param: str = '', if_null=None):
        try:
            attr = param.upper()
            value = getattr(self, attr, if_null)
            
            field_def = self.__dataclass_fields__.get(attr, None)

            if field_def:
                if field_def.default_factory is not MISSING:
                    new_val = field_def.default_factory()
                elif field_def.default is not MISSING:
                    new_val = field_def.default
                else:
                    new_val = None
                setattr(self, attr, new_val)
            else:
                setattr(self, attr, None)  # fallback if field isn't defined

            return value
        except Exception:
            log_exception(False)
            return if_null

    def update(self, **kwargs):
        try:
            for param, val in kwargs.items():
                setattr(self, param.upper(), val)
        except Exception:
            log_exception(False)

    def clear(self, param: str = ''):
        try:
            attr = param.upper()
            field_def = self.__dataclass_fields__.get(attr, None)

            if field_def:
                if field_def.default_factory is not MISSING:
                    new_val = field_def.default_factory()
                elif field_def.default is not MISSING:
                    new_val = field_def.default
                else:
                    new_val = None
                setattr(self, attr, new_val)
            else:
                setattr(self, attr, None) 

        except Exception:
            log_exception(False)

    def configure_network_defaults(self):
        try:
            self.MAXIMUM_DOWNTIME = 360
            self.MAX_REPOS_DRIV_MIN = 270
            self.DOUBLE_MAN_SHIFT_DUR = 990
            self.LIST_BREAK_MIN = [0, 30, 60]
            self.DRIVING_TIME_B4_BREAK = 270
            self.MIN_BREAK_TIME_WORKING = 30
            self.WORKING_TIME_B4_BREAK = 360
            self.MIN_BREAK_TIME = 60
            self.MAX_TOUR_DUR = 720
            self.MAX_DRIVING_DUR = 540
        except Exception:
            log_exception(False)

    def reset(self):
        """
        Reset all attributes to their default values as defined in the dataclass.
        """
        try:
            # create a fresh instance (bypassing the singleton behavior)
            defaults = super(UIParams, self.__class__).__call__()
            
            for field_name in self.__dataclass_fields__:
                setattr(self, field_name, getattr(defaults, field_name))
        
        except Exception as e:
            log_exception(False, remarks=f"Could not reset UIParams! {e}")


UI_PARAMS = UIParams.get_instance()
