from collections import defaultdict
from dataclasses import MISSING, dataclass, field
from pathlib import Path
from typing import Dict, List, Set
from lion.config.paths import LION_OPTIMIZATION_PATH
from lion.shift_data.shift_data import secure_copy
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception
from lion.utils.safe_copy import secure_copy
from lion.utils.singleton_meta import SingletonMeta


@dataclass
class OptimizationParams(metaclass=SingletonMeta):

    DICT_DRIVERS_PER_PAGE: Dict= field(default_factory=dict)
    SET_IMPACTED_SHIFTS: Set[str]= field(default_factory=set)
    LIST_FILTERED_DRIVERS_ALL_WEEK: List[str]= field(default_factory=list)
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

    OPTIMIZATION_REP_DAY: str = 'Wed'
    OPTIMIZATION_WEEKDAYS: List[str] = field(default_factory=lambda: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
    
    EXCL_DBLMAN: bool = True
    LIST_INFEASIBLE_SHIFT_IDS: List[int] = field(default_factory=list)
    SETOF_MOVEMENTS_IN_SCOPE: Set[int] = field(default_factory=set)
    SETOF_SHIFT_IDS_IN_SCOPE: Set[int] = field(default_factory=set)
    SETOF_EXCLUDED_MOVEMENTS_FROM_OPT: Set[int] = field(default_factory=set)
    SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT: Set[int] = field(default_factory=set)
    LIST_FILTERED_SHIFT_IDS: List[str] = field(default_factory=lambda: UI_PARAMS.LIST_FILTERED_SHIFT_IDS)
    USER_VEHICLE_ID: int = 0
    RUNNING_STRATEGIC_OPT: bool = False
    DBLMAN_RUNTIME_LIMIT: int = 265
    SCHEDULE_EMPLOYED_FLAG: bool = False
    EXCLUDED_LOCS: List[str] = field(default_factory=list) # list of locations to be excluded from lion.optimization specified by the user
    LION_TEMP_OPTIMIZED_SCN_NAME: str = ''
    DCT_DRIVERLOCS_PER_LANE: Dict[int, Set[str]] = field(default_factory=lambda: defaultdict(set))
    APPLY_MAX_DRIVERS_PER_LOC: bool = False
    DCT_DRIVER_LOCS_PER_LANE: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC: Dict[str, int] = field(default_factory=dict)
    DCT_SUBCO_DRIVERS_COUNT_PER_LOC: Dict[str, int] = field(default_factory=dict)
    SET_DRIVER_LOCS: Set[str] = field(default_factory=set)
    DCT_DRIVERS_COUNT_PER_LOC: Dict[str, int] = field(default_factory=dict)
    DCT_MOVEMENTS_TO_OPTIMIZE: Dict[int, dict] = field(default_factory=dict)
    DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC: Dict[str, Set[int]] = field(default_factory=lambda: defaultdict(set))

    APPLY_MAX_DRIVER_CNT: bool = False
    USER_LOADED_MOVEMENTS_FLAG: bool = False
    FORCE_LOAD_MOVEMENTS: bool = False
    RUN_EXTENDED_OPTIMIZATION: bool = False
    DCT_LANE_RUNTIMES_INFO: Dict[str, dict] = field(default_factory=lambda: defaultdict(set)) 

    DCT_CLOSE_BY_DRIVER_LOCS: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    SETOF_DOUBLEMAN_MOVEMENTS: Set[int] = field(default_factory=set)
    SCHEDULE_DBLMAN_MOVS: bool = False
    N_TOP_CLOSEST_DRIVER_LOC: int = 10

    MAXDOWNTIME_MAXREPOSMIN: List[int] = field(default_factory=lambda: [90, 120])
    MIP_SOLVER: str = 'Gurobi'
    DOUBLE_MAN_SHIFT_DUR: int = 990

    LOC_CAPACITY_LIMIT: int = 200

    def get(self, param: str = '', if_null=None):
        try:
            return secure_copy(getattr(self, param.upper(), if_null))
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


    def reset(self):
        try:
            for field_name, field_def in self.__dataclass_fields__.items():
                if field_def.default_factory is not MISSING:
                    setattr(self, str(field_name).upper(), field_def.default_factory())
                elif field_def.default is not MISSING:
                    setattr(self, str(field_name).upper(), field_def.default)
                else:
                    setattr(self, str(field_name).upper(), None)
        except Exception:
            log_exception(False)
    
OPT_PARAMS = OptimizationParams()

# list_filtered_drivers = UI_PARAMS.get(param='list_filtered_drivers', if_null=[])
# dict_drivers_per_page = UI_PARAMS.DICT_DRIVERS_PER_PAGE
# set_impacted_shifts = UI_PARAMS.get(param='set_impacted_shifts', if_null=set())
# hide_fixed = UI_PARAMS.get(param='hide_fixed', if_null=False)
# dct_cached_info = UI_PARAMS.DCT_CACHED_INFO
# page_num = UI_PARAMS.get(param='page_num', if_null=1)
# dct_traffic_type_colors = UI_PARAMS.get(param='dct_traffic_type_colors', if_null=False)
# filtering_wkdays = UI_PARAMS.get(param='filtering_wkdays', if_null=['Mon'])
# bar_width = UI_PARAMS.get(param='bar_width', if_null='45;40;35')