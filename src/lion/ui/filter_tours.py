from flask import logging
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_index import ShiftIndex
from sqlalchemy import and_
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.ui.options import refresh_options
from lion.logger.exception_logger import return_exception_code

def apply_filters():

    """
        Applies user-selected filters to the list of available driver shifts, updating UI parameters and filtered results.
        This function processes multiple filters set by the user, such as vehicle type, location codes, utilisation range and
        fixed shifts, to refine the list of driver shifts displayed in the UI. It updates relevant UI parameters,
        handles pagination, and manages the filtered shift IDs. The function also ensures that certain shifts (IDs 1 and 2)
        are excluded from the results and clears vehicle filters after use. If any errors occur during filtering, an exception
        handler returns an appropriate error code.
        Returns:
            dict: An empty dictionary on successful filtering, or an error code dictionary if an exception occurs.    
    """

    dict_drivers_per_page = {}
    list_filtered_drivers = []
    filtering_loc_codes= []
    selected_vehicles = []
    setof_impacted_shifts = set()

    try:

        if not UI_SHIFT_DATA.optimal_drivers:
            logging.error("No optimal drivers found.")
            return {}

        if UI_PARAMS.LIST_FILTERED_SHIFT_IDS:
            list_filtered_drivers.extend(UI_PARAMS.LIST_FILTERED_SHIFT_IDS)
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = []

        if UI_PARAMS.FILTERING_VEHICLES:
            selected_vehicles.extend(
                [int(vt) for vt in UI_PARAMS.FILTERING_VEHICLES])

            UI_PARAMS.FILTERING_VEHICLES = []

        if UI_PARAMS.FILTERING_LOC_CODES:
            filtering_loc_codes.extend(UI_PARAMS.FILTERING_LOC_CODES)
            UI_PARAMS.FILTERING_LOC_CODES = []

        if not list_filtered_drivers:
            list_filtered_drivers = [d for d, in DriversInfo.query.with_entities(
                DriversInfo.shift_id).filter(DriversInfo.shift_id > 2).all()]

        if filtering_loc_codes:

            list_filtered_drivers = [d for d, in DriversInfo.query.with_entities(DriversInfo.shift_id).filter(
                and_(DriversInfo.ctrl_loc.in_(filtering_loc_codes),
                        DriversInfo.shift_id.in_(list_filtered_drivers))).all()]

        if selected_vehicles:

            if list_filtered_drivers:
                list_filtered_drivers = [d for d, in DriversInfo.query.with_entities(DriversInfo.shift_id).filter(
                    and_(DriversInfo.vehicle.in_(selected_vehicles),
                            DriversInfo.shift_id.in_(list_filtered_drivers))).all()]
                
        if UI_PARAMS.UTILISATION_RANGE[0] > 0 or UI_PARAMS.UTILISATION_RANGE[1] < 100:

            if list_filtered_drivers:

                _shift_ids = UI_SHIFT_DATA.get_shifts_in_utilisation_range(
                    utilisation_range=UI_PARAMS.UTILISATION_RANGE)

                list_filtered_drivers = [
                    x for x in list_filtered_drivers if x in _shift_ids]

        if UI_PARAMS.HIDE_FIXED:

            if list_filtered_drivers:

                _shift_ids = set(UI_SHIFT_DATA.dct_fixed_optimal_drivers)
                list_filtered_drivers = [x for x in list_filtered_drivers if x not in _shift_ids]

            UI_PARAMS.HIDE_FIXED = False

        if list_filtered_drivers:
            dict_drivers_per_page = ShiftIndex.get_page_shifts(
                dct_shift_ids=DriversInfo.to_sub_dict(shift_ids=list_filtered_drivers), 
                pagesize=UI_PARAMS.PAGE_SIZE)

        if 1 in list_filtered_drivers:
            list_filtered_drivers.remove(1)

        if 2 in list_filtered_drivers:
            list_filtered_drivers.remove(2)

        UI_PARAMS.ALL_WEEK_DRIVERS_FILTERED = list_filtered_drivers
        UI_PARAMS.LIST_FILTERED_SHIFT_IDS = list_filtered_drivers
        UI_PARAMS.DICT_DRIVERS_PER_PAGE = dict_drivers_per_page
        UI_PARAMS.SET_IMPACTED_SHIFTS = setof_impacted_shifts
        UI_PARAMS.PAGE_NUM = UI_PARAMS.PAGE_NUM
        UI_PARAMS.PAGE_SIZE = UI_PARAMS.PAGE_SIZE
        UI_PARAMS.FILTERING_LOC_CODES = filtering_loc_codes

        refresh_options()

        return {}

    except Exception:
        return return_exception_code(popup=False, remarks='Filtering shifts failed!')