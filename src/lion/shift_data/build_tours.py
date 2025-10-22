from lion.algorithms.depth_first_search import DEPTH_FIRST_SEARCH
from lion.graph.build_connections import CONNECTION_TREE
from lion.orm.drivers_info import DriversInfo
from lion.shift_data.add_driver_loc import ADD_DRIVER
from lion.shift_data.exceptions import EXCEPTION_HANDLER
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.tour.tour_analysis import UI_TOUR_ANALYSIS
from lion.shift_data.shift_data import UI_SHIFT_DATA as active_shift_data
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception

def return_output(output=None, message=''):
    EXCEPTION_HANDLER.update(message)
    return output

def build(**kwargs):

    try:

        shift_id = kwargs.get('shift_id', 0)
        list_of_sorted_loaded_movements = kwargs.get('list_of_sorted_loaded_movements', [])
        capture_infeas_remarks = kwargs.get('capture_infeas_remarks', False)
        is_doubleman = kwargs.get('is_doubleman', False)
        report_exception = kwargs.get('report_exception', True)

        dct_drivers = DriversInfo.to_dict()

        _local_exceptions = ''

        if not list_of_sorted_loaded_movements:
            raise ValueError('No loaded movement was provided!')

        dict_tour_with_drivers = {}

        __list_break_min = [0]
        __list_of_movements = []
        __list_of_movements.extend(list_of_sorted_loaded_movements)
        __shift_vehicle = active_shift_data.optimal_drivers[shift_id].get(
            'vehicle', 1)

        shiftname = dct_drivers[shift_id]['shiftname']

        DEPTH_FIRST_SEARCH.reset()
        UI_MOVEMENTS.list_break_min = __list_break_min
        UI_MOVEMENTS.vehicle = __shift_vehicle
        UI_MOVEMENTS.shift = shiftname
        UI_MOVEMENTS.shift_id = shift_id

        CONNECTION_TREE.reset()
        CONNECTION_TREE.reset_default_network_params()

        vehicle = dct_drivers[shift_id]['vehicle']
        _is_doubleman = is_doubleman or DriversInfo.is_doubleman(shift_id=shift_id)
        is_driver_home_base = dct_drivers.get(
            shift_id, {}).get('hbr', True)

        UI_PARAMS.SHIFT_INFO = ';'.join([str(is_driver_home_base), str(_is_doubleman), str(vehicle)])

        ADD_DRIVER.reset()
        ADD_DRIVER.initialize_data_dump()
        
        while not dict_tour_with_drivers:

            dict_tour_with_drivers = {}
            UI_MOVEMENTS.list_break_min = __list_break_min
            CONNECTION_TREE.echo = True

            # Construct tours with drivers
            CONNECTION_TREE.set_input_movements = set(__list_of_movements)
            CONNECTION_TREE.build_connection_tree()
            DEPTH_FIRST_SEARCH.keep_tours_with_all_loaded_movements_only = True
            DEPTH_FIRST_SEARCH.connection_tree = CONNECTION_TREE

            DEPTH_FIRST_SEARCH.construct_tours(apply_double_man_rules=is_doubleman)

            ADD_DRIVER.add_drivers(dct_tours_data=DEPTH_FIRST_SEARCH.dct_tours_data, 
                                        driver_loc=dct_drivers[shift_id]['start position'],
                                        capture_infeas_remarks=capture_infeas_remarks,
                                        shift_id=shift_id)
            
            dict_tour_with_drivers.update(ADD_DRIVER.dict_tours_with_drivers)

            if __list_break_min.pop():
                if not DEPTH_FIRST_SEARCH.dct_tours_data:
                    _local_exceptions = f"No tour could be built.\n{
                        _local_exceptions}"

                break

            __list_break_min = [0, 30, 60]

        list_tour_with_drivers = list(dict_tour_with_drivers)
        if not list_tour_with_drivers:

            dct_tour = {}
            if capture_infeas_remarks:

                if ADD_DRIVER.dct_remarks_per_tour:

                    __list_t = set(ADD_DRIVER.dct_remarks_per_tour)
                    _local_exceptions = '\n'.join(
                        ADD_DRIVER.dct_remarks_per_tour[t] for t in __list_t)
                else:
                    __status_report = f"The tour could not not built but no infeasibility was reported!"
                    __status_report = f"{
                        __status_report} This could be caused by parameters such as down-time duration, turnaround-times, etc."

                    _local_exceptions = f"{__status_report}\n{_local_exceptions}"

            return return_output(output={}, message=_local_exceptions if report_exception else '')
        else:
            dct_tour = dict_tour_with_drivers.pop(list_tour_with_drivers[0])

        if dct_tour:

            dct_tour.update({'shift_id': shift_id})
            dct_tour.shiftname = shiftname
            dct_tour = UI_TOUR_ANALYSIS.calculate_cost(
                dct_tour)

        else:
            _local_exceptions = f"{
                _local_exceptions}; dct_tour was empty"

        if not dct_tour:
            _local_exceptions = f"cost went wrong\n{_local_exceptions}"

    except Exception:
        __err = log_exception(
            popup=False, remarks='The shift %s could not be built.' % shiftname)

        _local_exceptions = f"Error occured: {__err}\n{_local_exceptions}"
        
        dct_tour = {}

    return return_output(output=dct_tour, message=_local_exceptions if report_exception else '')
