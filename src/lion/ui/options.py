from os import getenv
from lion.bootstrap.constants import CALENDAR_DATE_FROM, TAG_NAME
from lion.config.js_modification_trigger import LATEST_JS_MODIFICATION_TIME
from lion.orm.location import Location
from lion.orm.operators import Operator
from lion.orm.user_params import UserParams
from lion.ui.basket import basket_shifts
from lion.ui.basket.pre_load_basket_shifts import pre_load_my_shifts_in_basket
from lion.ui.pushpins import PUSHPIN_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import return_exception_code
from lion.create_flask_app.create_app import LION_FLASK_APP

def update_all_locs(_dict_footprint):

    if _dict_footprint:

        _all_locs = sorted(list(_dict_footprint.keys()))
        _all_locs = [x + ' - ' + _dict_footprint[x].get('location_name', 'N/A')
                                for x in _all_locs if x in set(_dict_footprint)]
                        
        return _all_locs
    
    return []

def refresh_options(**kwargs):

    try:

        dct_options = UI_PARAMS.OPTIONS
        UI_PARAMS.configure_network_defaults()

        _dict_footprint = kwargs.get('dict_footprint', {})

        if _dict_footprint:
            _all_locs = update_all_locs(_dict_footprint)

            if _all_locs:
                dct_options.update({'dict_footprint': _dict_footprint, 
                                    'no_cust_locations': [loc for loc in _dict_footprint.keys() if loc not in Location.get_customers()],
                                    'all_locs': list(_all_locs)})
            else:
                raise Exception(f"location data in options was not updated!")
    
            UI_PARAMS.OPTIONS.update(dct_options)
            return {}

        if kwargs:
            UI_PARAMS.OPTIONS.update(**kwargs)
            return {}

        my_shifts_in_basket = basket_shifts.get_basket_shift_ids()

        dct_options = {}
        n_all_drivers = len(UI_SHIFT_DATA.optimal_drivers)

        if not UI_SHIFT_DATA.optimal_drivers:
            n_all_drivers = 2

        _dict_footprint = Location.to_dict()
        _all_locs = update_all_locs(_dict_footprint)
        
        dct_options.update({"vsn": LATEST_JS_MODIFICATION_TIME,
                            'LION_BING_API_KEY': getenv('LION_BING_API_KEY'),
                            'n_drivers': len(set(UI_PARAMS.LIST_FILTERED_SHIFT_IDS)),
                            'weekday': '/'.join(UI_PARAMS.FILTERING_WKDAYS) if UI_PARAMS.FILTERING_WKDAYS else '',
                            'n_all_drivers': n_all_drivers - 2,
                            'n_pages': len(UI_PARAMS.DICT_DRIVERS_PER_PAGE),
                            'all_locs': list(_all_locs),
                            'no_cust_locations': [loc for loc in _all_locs if loc not in Location.get_customers()],
                            'zipcodes': [],
                            'traffic_types': sorted([x for x in UI_PARAMS.DCT_TRAFFIC_TYPE_COLORS if x.lower() != 'empty']),
                            'operators': Operator.list_operators(),
                            'dict_footprint': _dict_footprint,
                            'datetimefrom': CALENDAR_DATE_FROM,
                            'title': f"{TAG_NAME}/{LION_FLASK_APP.config['LION_USER_ROLE']}",
                            'traffic_type': 'Express',
                            'filtering_loc_codes': [] if len(UI_PARAMS.FILTERING_LOC_CODES) > 10 else UI_PARAMS.FILTERING_LOC_CODES,
                            'basket_drivers':  list(set(my_shifts_in_basket)) if my_shifts_in_basket else pre_load_my_shifts_in_basket(),
                            'page_num': UI_PARAMS.PAGE_NUM,
                            'utilisation_range': UI_PARAMS.UTILISATION_RANGE,
                            'page_size': UI_PARAMS.PAGE_SIZE,
                            'enable_logging': getenv('LOGGING_ENABLED', 'False') == 'True',
                            'enbl_zoom': bool(UserParams.get_param(param='enable_zoom', if_null=0)),
                            'dct_pushpins': PUSHPIN_DATA.get()})

        UI_PARAMS.OPTIONS = dct_options

    except Exception:
        return return_exception_code(popup=False)

    return {}

