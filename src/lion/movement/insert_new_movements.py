from lion.movement.translate_locstr_to_movs import generate_movements_from_loc_string
from lion.shift_data.shift_manager import SHIFT_MANAGER
from lion.ui.driver_ui import DRIVERS_UI
from lion.ui.chart import get_chart_data
from lion.utils.safe_copy import secure_copy
from lion.logger.exception_logger import return_exception_code


def insert_movements(**dct_params) -> dict:

    __movement_id = int(dct_params.get('movement_id',  0))
    __page_num = dct_params.get('page_num', 1)

    if __movement_id:

        try:
            DRIVERS_UI.add_movement_to_dump_area(list_m=[__movement_id])
            return get_chart_data(page_num=__page_num)
        except Exception:
            return return_exception_code(popup=False, 
                                    remarks='Updating modify_movement_details failed.')

    try:
        __co_con_times = [int(str(x).strip()) for x in str(
            dct_params.get('co_con_time',  '15')).replace(
                ';', ',').replace('|', ',').replace('/', ',').split(',')]

    except Exception:
        return return_exception_code(
            popup=False, remarks='Reading buffer time failed.')

    tu_dest = dct_params.get('tu_dest',  '').strip().upper()
    traffic_type = dct_params.get('traffic_type',  'Express')
    loc_string = dct_params.get('loc_string',  '').upper()
    VehicleType = int(dct_params.get('vehicle',  1))
    dep_day = dct_params.get('dep_day', 'Mon')

    time_stamp = str(loc_string).split('.').pop() or ''
    try:
        time_stamp = int(time_stamp)
    except Exception:
        return({'code': 400, 
                'error': f"Could not extract time from {loc_string}. Please provide a valid dep time (ex. ADX.DZ5.2230)"})

    try:

        DRIVERS_UI.initialize_user_changes()

        created_movement_ids = generate_movements_from_loc_string(
            loc_string=loc_string,
            tu_dest=tu_dest,
            day=dep_day,
            traffictype=traffic_type,
            vehicle=VehicleType,
            co_con_time=__co_con_times)
        
        excp_message = SHIFT_MANAGER.exception_message

        if excp_message not in ['', 'OK']:
            raise Exception(excp_message)

        DRIVERS_UI.add_movement_to_dump_area(
            list_m=list(created_movement_ids))

        __dct_page_chart_data = secure_copy(get_chart_data(page_num=__page_num))

        return __dct_page_chart_data

    except Exception:
        return return_exception_code(popup=False)

    # try:

    #     if __movement_id:
    #         active_shift_data.delete_movement(__movement_id)

    #     return __dct_page_chart_data

    # except Exception:
    #     return return_exception_code(popup=False)

