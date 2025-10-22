from datetime import datetime, timedelta
from lion.bootstrap.constants import LION_DATES
from lion.delta_suite.delta_logger import DELTA_LOGGER
from pandas import isnull


def build_temp_tour(**kwargs):

    lanes_with_no_runtime = []
    try:
        shift_id = kwargs.get('shift_id')
        m = kwargs.get('m')
        deptime = kwargs.get('deptime')
        depday = kwargs.get('depday')
        driving_time = kwargs.get('driving_time')
        loc_from = kwargs.get('loc_from')
        loc_to = kwargs.get('loc_to')
        dist = kwargs.get('dist')

        time_obj = datetime.strptime(
            f'0000{deptime}'[-4:], "%H%M").time()
        schedule_day = 'Mon'

        if isnull(driving_time):
            lanes_with_no_runtime.append(f"{m}: {loc_from}->{loc_to}")
            driving_time = 150
            dist = 100

        dep_date_time = datetime.combine(LION_DATES[schedule_day], time_obj) + timedelta(days=depday)

        dct_tour = {}
        dct_tour.update({
            'shift_id': shift_id,
            'driver': f"{loc_from}.{shift_id}",
            'movement_shift_pair': [(m, shift_id)],
            'list_loaded_movements': [m],
            'list_movements': [m],
            'dep_date_time': dep_date_time - timedelta(minutes=30),
            'arr_date_time': dep_date_time + timedelta(minutes=driving_time + 30),
            'shift_end_datetime': dep_date_time + timedelta(hours=12),
            'tour_cntry_from': 'FR',
            'is_complete': False,
            'tour_loc_from': loc_from,
            'tour_loc_string': '->'.join([loc_from, loc_to]),
            'total_dur': driving_time + 60,
            'tour_repos_dist': 0,
            'tour_input_dist': dist,
            'driving_time': driving_time,
            'input_driving_time': driving_time,
            'repos_driving_time': 0,
            'idle_time': 0,
            'break_time': 0,
            'is_feas': True,
            'is_fixed': False,
            'Source': 'LION',
            'dct_running_tour_data': {},
            'remark': 'Initial tour',
            'remark_fr': 'Initial tour',
            'notifications': '',
            'mouseover_info': '',
            'avg_utilisation': 0.01,
            'time_utilisation': driving_time * 100/720,
            'n_repos_movs': 0,
            'n_input_movs': 1,
            'interim_idle_times': [],
            'double_man': False
        })

        dct_tour['driver_loc_mov_type_key'] = dct_tour[
            'dep_date_time'].strftime('%H%M') + '->' + \
            dct_tour['tour_loc_string'] + '->' + \
            dct_tour['arr_date_time'].strftime('%H%M')

    except Exception as e:
        DELTA_LOGGER.log_exception(message=f"Error building tour: {str(e)}")
        return {}

    if lanes_with_no_runtime:
        DELTA_LOGGER.log_message(message=f"Building local_schedule_db has been completed! {'\n'.join(lanes_with_no_runtime)}")

    return dct_tour