import logging
from lion.changeovers import changeover_shifts
from lion.bootstrap.constants import MOVEMENT_TYPE_COLOR
from lion.logger.status_logger import log_message
from lion.orm.changeover import Changeover
from lion.orm.drivers_info import DriversInfo
from lion.orm.vehicle_type import VehicleType
from lion.tour.dct_tour import DctTour
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.ui.options import refresh_options
from lion.utils.safe_copy import secure_copy
from lion.utils.km2mile import km2mile
from lion.utils.minutes2hhmm_str import minutes2hhmm_str
from lion.logger.exception_logger import log_exception, return_exception_code
from lion.utils.remove_element import remove_element
from lion.utils.str_to_utc import str2UTC
from lion.utils.weekday_to_int import to_daystr


def get_chart_data(**dct_params):
    """
    This module returns data to display on the drag and drop UI (gantt chart). It builds a dict
    containing all the components required to visualize the selected shifts and their movements on the UI.

    Parameters:
    - dct_params (dict): A dictionary containing the parameters for retrieving the chart data.

    Returns:
    - dict: A dictionary containing the chart data to be rendred in gantt chart.

    Example Usage:
    chart_data = get_chart_data(drivers=[1, 2], page_num=1, shift_data=shift_data)
    """

    try:

        if not UI_SHIFT_DATA.optimal_drivers:

            UI_PARAMS.SET_IMPACTED_SHIFTS = set()
            UI_PARAMS.RIGHT_CLICK_ID=0

            return {}

        drivers = dct_params.get('drivers', [])
        page_num = int(dct_params.get('page_num', UI_PARAMS.PAGE_NUM))

        if not drivers:
            if page_num:

                if (UI_PARAMS.PAGE_NUM != page_num):
                    UI_PARAMS.PAGE_NUM = page_num

                drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE.get(page_num, [])
                refresh_options(page_num=page_num)

            else:
                if UI_SHIFT_DATA.optimal_drivers[1]['list_loaded_movements']:
                    disp_dump_area = True

        refresh_options()

        list_test_shifts = DriversInfo.get_test_shift_ids()
        list_test_shifts = [
            d for d in list_test_shifts if d in UI_SHIFT_DATA.optimal_drivers]

        dct_page_chart_data = {}
        disp_dump_area = False

        # if not drivers:
        #     if page_num:
        #         UI_PARAMS.PAGE_NUM = page_num
        #         refresh_options(page_num=page_num)
        #         drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE.get(page_num, [])

        #     else:
        #         if UI_SHIFT_DATA.optimal_drivers[1]['list_loaded_movements']:
        #             disp_dump_area = True

        [drivers.remove(shft) for shft in drivers
            if shft not in set(UI_SHIFT_DATA.optimal_drivers)]

        if UI_PARAMS.LIST_FILTERED_SHIFT_IDS and page_num:
            drivers = [
                d for d in drivers if d in UI_PARAMS.LIST_FILTERED_SHIFT_IDS]

        dct_bar_data_movements: dict = {}
        dct_bar_data_shifts: dict = {}
        dct_bar_data_operators: dict = {}

        if drivers:

            if UI_PARAMS.HIDE_FIXED:
                drivers = [d for d in drivers if not UI_SHIFT_DATA.optimal_drivers.get(
                    d, {}).get('is_fixed', False)]

            remove_element(drivers, 1)
            remove_element(drivers, 2)

            drivers = list(reversed(drivers))

        if list_test_shifts:

            for d in list_test_shifts:
                if d not in drivers:
                    drivers.append(d)
                else:
                    drivers.remove(d)
                    drivers.append(d)

        just_handled_shifts = UI_PARAMS.DCT_CACHED_INFO.get('just_handled_shifts', set())

        if just_handled_shifts:

            for d in just_handled_shifts:
                if d not in drivers:
                    drivers.append(d)
                else:
                    drivers.remove(d)
                    drivers.append(d)

        if page_num:
            drivers.append(1)
            drivers.append(2)

        elif disp_dump_area:
            drivers.append(1)

        bar_width = UI_PARAMS.BAR_WIDTH[0]

        __notifications = ''
        __drivers_with_issues = []
        driver_operators = []

        driver_names = []

        running_days = DriversInfo.get_running_days(shift_ids=drivers)

        _tmp_unique_movement_id = 1000
        _tmp_unique_brk_id = 10000
        for idx, d in enumerate(drivers, start=1):

            __driver_list_of_movements: list = []
            __dct_running_tour_data: dict = {}

            dys = running_days[d]
            dys = [x.lower() if x == 'Tue' else x for x in dys]

            str_running_days = '.'.join([x[0] for x in dys])

            __dct_driver = DctTour(**UI_SHIFT_DATA.optimal_drivers.get(
                d, {}))

            try:
                if not __dct_driver:

                    if d not in [1, 2]:
                        __dct_driver = UI_SHIFT_DATA.blank_shift(
                            shift_id=d)
                    else:
                        __dct_driver = UI_SHIFT_DATA.dct_movement_dump_area

                if __dct_driver.get('notifications', '') != '':
                    if d in UI_PARAMS.SET_IMPACTED_SHIFTS:
                        if __notifications == '':
                            __notifications = '%s: %s' % (
                                d, __dct_driver.get('notifications', ''))
                        else:
                            __notifications = '%s\n%s: %s' % (
                                __notifications, d, __dct_driver.get('notifications', ''))

                __is_fixed = __dct_driver.get('is_fixed', False)
                __is_feas = __dct_driver.get('is_feas', True)
                __vehicle = int(__dct_driver.get('vehicle', 0))

                vhcle = VehicleType.get_vehicle_name(__vehicle)
                __short_vhcle = VehicleType.get_vehicle_short_name(
                    __vehicle)

                __vehicle_type = '%d. %s' % (__vehicle, vhcle)
                __utilisation = __dct_driver.time_utilisation

                __time_utilisation = "{:.0f}%".format(
                    __utilisation) if __utilisation > 0 else ''

                __operator = DriversInfo.get_operator(shift_id=d)
                _dbl_man = __dct_driver.get(
                    'double_man', False) or DriversInfo.is_doubleman(shift_id=d)

                __short_operator = 'Operator' if d == 1 else (
                    'Employed' if __operator == 'FedEx Express' else (
                        __operator if len(__operator) <= 12 else __operator[:11] + '.'))

                __short_operator = __short_operator if __short_operator in [
                    '', 'Operator'] else f'{__short_operator} ({__short_vhcle})'

                driver_operators.append(__short_operator)

                __siftnote = __dct_driver.get('shift_note', '')
                dblmnstr = '²' if _dbl_man else ''
                shiftnotestr = "ᴺ" if __siftnote != '' else ''

                driver_names.append(f"{__dct_driver.driver}{
                                    dblmnstr}{shiftnotestr}")

                if __is_fixed:
                    __shift_color = MOVEMENT_TYPE_COLOR['fixed']
                elif __is_feas:
                    __shift_color = MOVEMENT_TYPE_COLOR['shift']
                else:
                    __shift_color = MOVEMENT_TYPE_COLOR['infeas']

                __dct_running_tour_data.update(__dct_driver.get(
                    'dct_running_tour_data', {}))

                __driver_list_of_movements.extend(
                    __dct_driver.list_movements)

                if __dct_running_tour_data and __driver_list_of_movements:
                    __last_m = __driver_list_of_movements[-1]
                    __dct_running_tour_data.get(
                        __last_m, {}).update({'poa': 0})

                str_tour_loc_string: str = __dct_driver.get(
                    'tour_loc_string', '')

                if d in [2, 1]:

                    dct_bar_data_shifts[d] = {}

                    if 'dep_date_time' not in __dct_driver:
                        __dct_dump = UI_SHIFT_DATA.dct_movement_dump_area
                        __dct_dump.update(__dct_driver)
                        __dct_driver = secure_copy(__dct_dump)

                    x_UTC_shift = str2UTC(
                        strDate=__dct_driver['dep_date_time'].strftime(
                            '%Y-%m-%d %H:%M')
                    )

                    x2_UTC_shift = str2UTC(
                        strDate=__dct_driver['shift_end_datetime'].strftime(
                            '%Y-%m-%d %H:%M')
                    )

                    shift_data: dict = {
                        'x': x_UTC_shift,
                        'x2': x2_UTC_shift,
                        't1': __dct_driver['dep_date_time'].strftime('%Y-%m-%d %H:%M')[-5:],
                        't2': __dct_driver['shift_end_datetime'].strftime('%Y-%m-%d %H:%M')[-5:],
                        'from': "",
                        'to': "Shift",
                        'tour_locs_string': '',
                        'label_info': '',
                        'y': idx,
                        'id': d,
                        'object_id': d,
                        'shift_id': d,
                        'driver': __dct_driver.driver,
                        'mouseover_info': '',
                        'vehicle': 'N/A',
                        'tu': 'N/A',
                        'rdays': '',
                        'dragDrop': {
                            'draggableX': False,
                            'draggableY': False
                        },
                        'color': '#e8e8e8',
                        'maxPointWidth': 50,
                        'strID': __dct_driver.get('co_loc_string', 'N/A'),
                        'pointWidth': bar_width
                    }
                    dct_bar_data_shifts[d] = shift_data

                    dct_bar_data_operators[__short_operator] = {
                        'x': 0, 'x2': 0, 'y': idx, 'pointWidth': 0}

                if d in [2]:
                    pass
                else:

                    x_UTC_shift = str2UTC(
                        strDate=__dct_driver['dep_date_time'].strftime('%Y-%m-%d %H:%M'))
                    x2_UTC_shift = str2UTC(
                        strDate=__dct_driver['shift_end_datetime'].strftime('%Y-%m-%d %H:%M'))

                    __rmrks = __dct_driver.get(
                        'remark', 'No info available!')

                    idle_time = __dct_driver.get('idle_time', 0)
                    break_time = __dct_driver.get('break_time', 0)

                    if idle_time:
                        __rmrks = f"{__rmrks}. Total Idle time: {idle_time} min"

                    if break_time:
                        __rmrks = f"{__rmrks}. Total Break time: {break_time} min."

                    __rmrks = '%s (%s):\n%s' % (
                        __dct_driver.driver, __operator, __rmrks)

                    msover = __dct_driver.get('mouseover_info', '')
                    # msover = f"{msover}. Total Idle time: {idle_time} min. Total Break time: {break_time} min."

                    if __siftnote != '':
                        __rmrks = '%s\n\n%s' % (__rmrks, __siftnote)

                    shift_data: dict = {
                        'x': x_UTC_shift,
                        'x2': x2_UTC_shift,
                        'depday': __dct_driver['dep_date_time'].strftime('%a'),
                        't1': __dct_driver['dep_date_time'].strftime('%Y-%m-%d %H:%M')[-5:],
                        't2': __dct_driver['shift_end_datetime'].strftime('%Y-%m-%d %H:%M')[-5:],
                        # __dct_driver['dep_date_time'].strftime('%a %H:%M'),
                        'dt1': to_daystr(__dct_driver['dep_date_time']),
                        # __dct_driver['shift_end_datetime'].strftime('%a %H:%M'),
                        'dt2': to_daystr(__dct_driver['shift_end_datetime']),
                        'from': "",
                        'to': "Shift",
                        'label_info': '',
                        'vehicle': __vehicle_type,
                        'tu': 'N/A',
                        'mouseover_info':  msover,
                        'remark': __rmrks,
                        'loc_string':  ("Shift-Fixed" if __is_fixed else "Shift") + ': ' + str_tour_loc_string,
                        'y': idx,
                        'id': d,
                        'object_id': d,
                        'shift_id': d,
                        'driver': __dct_driver.driver,
                        'strID': __dct_driver.get('co_loc_string', 'N/A'),
                        'operator': __operator,
                        'time_utilisation': __time_utilisation,
                        # 'linehaul_id': '',
                        'rdays': str_running_days,
                        'dragDrop': {
                            'draggableX': False,
                            'draggableY': False
                        },
                        'color': __shift_color,
                        'maxPointWidth': 50,
                        'pointWidth': bar_width
                    }
                    dct_bar_data_shifts[d] = shift_data

                    dct_bar_data_operators[__short_operator] = {
                        'x': 0, 'x2': 0, 'y': idx, 'pointWidth': 0}

                    del shift_data

                if __driver_list_of_movements:

                    __tmp_movements = [int(x)
                                        for x in __driver_list_of_movements]

                    del __driver_list_of_movements

                    for m in __tmp_movements:

                        _tmp_unique_movement_id += 1

                        if __dct_running_tour_data.get(m, {}).get('Break', 0):
                            # if __dct_running_tour_data.get(m, {}).get('edatetime', 0):

                            dct_m_break = __dct_running_tour_data.get(
                                m, {})

                            if dct_m_break:

                                _tmp_unique_brk_id += 1
                                dct_m_break['strDepDateTime'] = dct_m_break['sdatetime'].strftime(
                                    '%Y-%m-%d %H:%M')

                                dct_m_break['strArrDateTime'] = dct_m_break['edatetime'].strftime(
                                    '%Y-%m-%d %H:%M')

                                x_UTC = str2UTC(
                                    dct_m_break['strDepDateTime'])
                                x2_UTC = str2UTC(
                                    dct_m_break['strArrDateTime'])

                                # __Lhid = ''

                                m_data: dict = {
                                    'x': x_UTC,
                                    'x2': x2_UTC,
                                    'depday': '',
                                    'traffic_type': 'BRK',
                                    'dt2': to_daystr(dct_m_break['edatetime']),
                                    'dt1': to_daystr(dct_m_break['sdatetime']),
                                    't1': dct_m_break['strDepDateTime'][-5:],
                                    't2': dct_m_break['strArrDateTime'][-5:],
                                    'from': '',
                                    'to': '',
                                    'tour_locs_string': '',
                                    'loc_string': '',
                                    'changeover_id': 0,
                                    'y': idx,
                                    'id': _tmp_unique_brk_id,
                                    'object_id': _tmp_unique_brk_id,
                                    'remark': '',
                                    'mouseover_info': '',
                                    'vehicle': __vehicle_type,
                                    'tu': 'N/A',
                                    'shift_id': d,
                                    'driver': __dct_driver.driver,
                                    'Leg': 'N/A',
                                    'label': 'BRK',
                                    'dragDrop': {
                                        'draggableX': False,
                                        'draggableY': False
                                    },
                                    'color': MOVEMENT_TYPE_COLOR['break'],
                                    'maxPointWidth': 50,
                                    'pointWidth': bar_width
                                }

                                dct_bar_data_movements[_tmp_unique_brk_id] = m_data
                                del m_data

                        dct_m = UI_SHIFT_DATA.dict_all_movements.get(
                            m, {})

                        if dct_m:

                            __loc_str = dct_m.linehaul_id

                            shifts_ids = []
                            _co_str, legs_str = Changeover.get_movement_loc_string(
                                movment_id=m)

                            if _co_str != '':
                                __loc_str = _co_str
                                shifts_ids = changeover_shifts.get_changeover_shiftids(loc_string=_co_str)

                            _co_indicator = '*' if shifts_ids else ''
                            str_shifts = '/'.join(
                                str(DriversInfo.get_shift_name(shift_id=id)) for id in shifts_ids) if shifts_ids else dct_m.shift

                            depdaytimestr = to_daystr(
                                dct_m['DepDateTime'])
                            arrdaytimestr = to_daystr(
                                dct_m['ArrDateTime'])

                            __mouseover_info = ''

                            __tu = dct_m.tu
                            __tu = 'N/A' if __tu in ['nan',
                                                        'N/A', ''] else __tu

                            __mouseover_info = __mouseover_info + \
                                'Loc_string: %s ----- ' % (__loc_str)

                            __mouseover_info = __mouseover_info + \
                                'DepTime: %s ----- ' % (
                                    depdaytimestr)

                            __mouseover_info = (
                                __mouseover_info + 'Arrival: %s ----- ' % (arrdaytimestr))

                            __mouseover_info = __mouseover_info + \
                                'Lane: %s ----- ' % (
                                    dct_m['From'] + '.' + dct_m['To'])

                            __mouseover_info = __mouseover_info + \
                                'TrafficType: %s ----- ' % (
                                    dct_m['TrafficType'])

                            __mouseover_info = __mouseover_info + \
                                'Vehicle: %s ----- ' % (__short_vhcle)

                            __mouseover_info = __mouseover_info + \
                                'Operator: %s ----- ' % (__operator)

                            __mouseover_info = __mouseover_info + \
                                f"Leg: {legs_str} ----- "

                            __mouseover_info = __mouseover_info + \
                                'TU: %s ----- ' % (__tu)

                            __mouseover_info = __mouseover_info + \
                                'Shifts: %s ----- ' % (str_shifts)

                            # '/'.join([str(x) for x in dct_m.get(
                            #     'ChgOverShifts', [dct_m.get('shift', 'N/A')])]))

                            __mouseover_info = __mouseover_info + \
                                'strID: %s ----- ' % (dct_m.str_id)

                            __mouseover_info = __mouseover_info + \
                                'Runtime (excl. Turn.): %s ----- ' % (
                                    minutes2hhmm_str(dct_m['DrivingTime']))

                            __mouseover_info = __mouseover_info + \
                                'Mileage: %d' % (
                                    km2mile(dct_m['Dist']))

                            if __dct_running_tour_data.get(m, {}):

                                __mouseover_info = __mouseover_info + '\nTDT:   %s' % (
                                    minutes2hhmm_str(__dct_running_tour_data[m]['tdt']))

                                __mouseover_info += '\nTWT:   %s' % (
                                    minutes2hhmm_str(__dct_running_tour_data[m]['twt']))

                                if __dct_running_tour_data[m]['poa'] > 0:
                                    __mouseover_info += '\nPoA:   %s' % (
                                        minutes2hhmm_str(__dct_running_tour_data[m]['poa']))

                                if __dct_running_tour_data[m].get('break', 0) > 0:
                                    __mouseover_info += '\nBreak:   %s' % (
                                        minutes2hhmm_str(__dct_running_tour_data[m].get('break', 0)))

                                __mouseover_info += '\nDT before break: %s' % (
                                    minutes2hhmm_str(__dct_running_tour_data[m]['tdtb4brk']))

                                __mouseover_info += '\nWT before break: %s' % (
                                    minutes2hhmm_str(__dct_running_tour_data[m]['twtb4brk']))

                            dct_m['strDepDateTime'] = dct_m['DepDateTime'].strftime(
                                '%Y-%m-%d %H:%M')

                            dct_m['strArrDateTime'] = dct_m['ArrDateTime'].strftime(
                                '%Y-%m-%d %H:%M')

                            x_UTC = str2UTC(
                                dct_m['strDepDateTime'])
                            x2_UTC = str2UTC(
                                dct_m['strArrDateTime'])

                            __traffic_type = dct_m['TrafficType']
                            __mov_color = UI_PARAMS.DCT_TRAFFIC_TYPE_COLORS.get(
                                __traffic_type, None)

                            __m_vehicle = int(dct_m['VehicleType'])

                            m_data: dict = {
                                'x': x_UTC,
                                'x2': x2_UTC,
                                'depday': dct_m['DepDateTime'].strftime('%a'),
                                'traffic_type': __traffic_type,
                                'dt2': arrdaytimestr,
                                'dt1': depdaytimestr,
                                't1': dct_m['strDepDateTime'][-5:],
                                't2': dct_m['strArrDateTime'][-5:],
                                'from': dct_m['From'],
                                'to': dct_m['To'],
                                'tour_locs_string': str_tour_loc_string,
                                'loc_string': __loc_str,

                                'label': '.'.join([dct_m['From'], dct_m['To']]) + _co_indicator,
                                'Leg': f"{legs_str}",
                                'y': idx,
                                'object_id': m,
                                'id': _tmp_unique_movement_id,
                                'remark': '',
                                'mouseover_info': __mouseover_info,
                                'shift_id': d,
                                'driver': __dct_driver.driver,
                                'vehicle': '%d. %s' % (__m_vehicle, VehicleType.get_vehicle_name(__m_vehicle)),
                                'tu': __tu,
                                'mileage': km2mile(dct_m['Dist']),
                                'driving_time': minutes2hhmm_str(dct_m['DrivingTime']),
                                'strID': dct_m.str_id,
                                'dragDrop': {
                                    'draggableX': True, #dct_m.get('draggableX', False),
                                    'draggableY': dct_m.get('draggableY', False),
                                },
                                'color': MOVEMENT_TYPE_COLOR[dct_m.get(
                                    'color_category', 'Unknown')] if __mov_color is None else __mov_color,
                                'maxPointWidth': 50,
                                'pointWidth': bar_width
                            }

                            dct_bar_data_movements[_tmp_unique_movement_id] = m_data
                            del m_data

                            if x2_UTC > x2_UTC_shift:
                                dct_bar_data_shifts[d]['mouseover_info'] = dct_bar_data_shifts[d]['mouseover_info'] + \
                                    'Driver: {} - The shift is too long due to the movement {} !'.format(
                                        d, '.'.join([dct_m['From'], dct_m['To']]))

                        else:
                            log_message(message='No data was found for movement {}'.format(m),
                                        module_name='DnD.py/get_chart_data')

                        del dct_m

            except Exception:
                log_exception(False)
                __drivers_with_issues.append(d)

        driver_names.insert(0, '')
        driver_operators.insert(0, '')
        drivers.insert(0, 0)

        if __drivers_with_issues:
            __notifications = '%s. %s' % (__notifications, 'The following shifts not laoded: %s' % (
                ';'.join([str(id) for id in __drivers_with_issues])))

        dct_page_chart_data['dct_bar_data_movements'] = secure_copy(
            dct_bar_data_movements)
        dct_page_chart_data['dct_bar_data_shifts'] = secure_copy(
            dct_bar_data_shifts)

        dct_page_chart_data['tData'] = []
        dct_page_chart_data['tData_operators'] = []

        dct_page_chart_data['changed_drivers'] = list(
            DriversInfo.dct_shiftnames(shift_ids=UI_PARAMS.SET_IMPACTED_SHIFTS).values())
        dct_page_chart_data['new_drivers'] = []
        dct_page_chart_data['removed_drivers'] = []

        dct_page_chart_data['drivers'] = driver_names
        dct_page_chart_data['shift_ids'] = drivers

        dct_page_chart_data['driver_operators'] = driver_operators

        dct_page_chart_data['xAxis_range'] = [str2UTC(
            strDate=UI_SHIFT_DATA.xAxis_range_start.strftime('%Y-%m-%d %H:%M')),
            str2UTC(strDate=UI_SHIFT_DATA.xAxis_range_end.strftime('%Y-%m-%d %H:%M'))]

        if dct_page_chart_data['tData'] == []:

            tData: list = []  # tData = [{}, {}, ..., {}]
            tData_operators: list = []
            tData_ctrlers: list = []
            dct_chart_movements: dict = dct_page_chart_data['dct_bar_data_movements']
            dct_chart_shifts: dict = dct_page_chart_data['dct_bar_data_shifts']

            for shift_id in dct_chart_shifts.keys():
                tData.append(dct_chart_shifts[shift_id])

            for idx, oprt in enumerate(driver_operators):
                tData_operators.append(dct_bar_data_operators.get(
                    oprt, {'x': 0, 'x2': 0, 'y': idx}))

            for mov in dct_chart_movements.keys():
                tData.append(dct_chart_movements[mov])

            dct_page_chart_data['tData'] = tData
            dct_page_chart_data['tData_operators'] = tData_operators
            dct_page_chart_data['tData_ctrlers'] = tData_ctrlers

        dct_page_chart_data['options'] = UI_PARAMS.OPTIONS
        dct_page_chart_data['remarks'] = dct_params.get('remarks', '')
        dct_page_chart_data['notifications'] = __notifications
        dct_page_chart_data['popup'] = ''

        __flg = ''
        _shift_name = f"{
            UI_SHIFT_DATA.scn_name}{__flg} (Pg. {page_num}) - {len(UI_PARAMS.LIST_FILTERED_SHIFT_IDS)} shifts"

        if UI_PARAMS.FILTERING_WKDAYS:
            _shift_name = f"{'/'.join(UI_PARAMS.FILTERING_WKDAYS)}/{_shift_name}"

        dct_page_chart_data['shift_name'] = f"{_shift_name} Default"
        UI_PARAMS.SET_IMPACTED_SHIFTS = set()
        UI_PARAMS.RIGHT_CLICK_ID=0

        return dct_page_chart_data

    except Exception:
        UI_PARAMS.SET_IMPACTED_SHIFTS = set()
        return return_exception_code(popup=False, remark='Error when building schedule UI.')
