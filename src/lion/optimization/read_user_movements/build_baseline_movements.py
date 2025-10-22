from datetime import datetime, timedelta
from lion.movement.dct_movement import DictMovement
from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.read_user_movements.get_runtimes_info import get_temp_runtimes_info
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.read_user_movements.deptime_transformer import get_datetime
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.ui.ui_params import UI_PARAMS
from lion.utils.safe_copy import secure_copy

def build_baseline_dct_movements():
    """
    Builds baseline movement dictionaries for optimization.
    This function retrieves all movement records from the `LocalMovements` database table,
    processes each record to extract relevant movement information, and constructs a dictionary
    of movement objects (`dict_all_movements`). It also creates a subset dictionary
    (`dct_movements_to_optimize`) containing only those movements with `shift_id` equal to 0.

    For each movement, the function:

        - Parses movement attributes from the `str_id` field.
        - Retrieves or computes runtime and distance information.
        - Constructs a dictionary of movement properties, including scheduling, vehicle, and route details.
        - Handles special cases for empty (repositioning) movements.
        - Converts the dictionary into a `DictMovement` object and updates its string ID.
        - Adds the movement to the main and optimization dictionaries as appropriate.

    If any errors occur during processing, they are logged using `OPT_LOGGER`, and the function
    attempts to clear the results and log the error details.

    At the end, the function updates the global `UI_MOVEMENTS.dict_all_movements` and
    `OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE` with the constructed dictionaries.
    
    Raises:
        Exception: If errors are encountered during processing, an exception is raised and logged.
    """

    OPT_LOGGER.log_statusbar(message='Building baseline movement dictionaries for optimization ...')
    
    error_message = ''
    dict_all_movements = {}
    base_week_day = 'Mon'
    all_mov_records = ShiftMovementEntry.query.all()
    dct_movements_to_optimize = {}

    for movObj in all_mov_records:

        try:

            origin, dest, depday, deptime, vehicle, traffic_type = movObj.str_id.split(
                '|')

            depday = int(depday)
            vehicle = int(vehicle)
            mov_id = movObj.movement_id
            shift_id = movObj.shift_id

            dct_data = OPT_PARAMS.DCT_LANE_RUNTIMES_INFO.get('|'.join([origin, dest, str(vehicle)]),
                                                get_temp_runtimes_info(orig=origin, dest=dest, vehicle=int(vehicle)))

            if not dct_data:
                raise ValueError(f"No runtime data found for {origin}->{dest} with vehicle {vehicle}!")
            
            dist = dct_data['dist']
            driving_time = dct_data['runtime']

            loc_string = movObj.loc_string
            tu_dest = movObj.tu_dest

            locs = []

            if loc_string != '' and tu_dest == '':

                locs = loc_string.split('.')
                locs.pop()  # deptime
                tu_dest = locs.pop()

            dct_m = {}

            dct_m['weekday'] = base_week_day
            DepDateTime = get_datetime(
                depday=depday, deptime=deptime, schedule_day=base_week_day)

            if not DepDateTime:
                raise ValueError(
                    'Dep date time cannot be None!')

            if driving_time is None:
                raise ValueError('Driving time was None!')

            is_repos = traffic_type.lower() == 'empty'

            dct_m['DepDateTime'] = DepDateTime
            dct_m['ArrDateTime'] = DepDateTime + timedelta(
                minutes=driving_time)

            dct_m['MovementID'] = mov_id
            dct_m['From'] = origin
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['TrafficType'] = traffic_type
            dct_m['tu'] = tu_dest
            dct_m['loc_string'] = loc_string

            dct_m['shift_id'] = shift_id

            dct_m['draggableX'] = True
            dct_m['draggableY'] = False if is_repos else True
            dct_m['is_repos'] = is_repos

            dct_m['DrivingTime'] = driving_time

            dct_m['Utilisation'] = 0.01
            dct_m['PayWeight'] = 0
            dct_m['Pieces'] = 0
            dct_m['Capacity'] = 18000

            dct_m['Dist'] = dist

            dct_m['CountryFrom'] = UI_PARAMS.LION_REGION,

            dct_m['last_update'] = datetime.now().strftime(
                '%Y-%m-%d %H%M')

            dct_m = DictMovement(**dct_m)
            dct_m.update_str_id()

            dict_all_movements[mov_id] = dct_m

            if shift_id == 0:
                dct_movements_to_optimize[mov_id] = dct_m

        except Exception:
            error_message = f"{error_message}\nError: {OPT_LOGGER.log_exception(
                popup=False, remarks=f'Error when building {origin}->{dest}: {vehicle} movement!')}"
    
    if error_message:
        try:
            dict_all_movements = {}
            raise Exception(error_message)
        except Exception:
            OPT_LOGGER.log_exception(popup=False, remarks=error_message)

    if dict_all_movements:
        UI_MOVEMENTS.dict_all_movements = dict_all_movements

    OPT_LOGGER.log_statusbar(f"Number of movements to optimize: {len(dct_movements_to_optimize)}")
    
    if dct_movements_to_optimize:
        
        OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE = set(dct_movements_to_optimize.keys())
        OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE = secure_copy(dct_movements_to_optimize)
        OPT_PARAMS.SETOF_DOUBLEMAN_MOVEMENTS = set([m for m in set(dct_movements_to_optimize.keys()) 
                                                    if dct_movements_to_optimize[m]['DrivingTime'] >= OPT_PARAMS.DBLMAN_RUNTIME_LIMIT])