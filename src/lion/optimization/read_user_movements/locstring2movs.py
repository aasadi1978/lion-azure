from datetime import timedelta
from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.bootstrap.constants import LION_DATES, MOVEMENT_DUMP_AREA_NAME
from lion.orm.changeover import Changeover
from lion.optimization.orm.opt_movements import OptimizationMovements as OptMovements
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.utils.combine_date_time import combine_date_time
from lion.optimization.optimization_logger import OPT_LOGGER


def locstring2changeover(loc_string='',
                         weekday='Mon',
                         day='Mon',
                         running_days=[],
                         traffictype='Express',
                         vehicle=1,
                         tu_dest='',
                         co_con_time=15,
                         shift_id=1,
                         dep_day=0):

    """
    Parses a location string representing a sequence of movements, generates movement records, and handles changeovers.
    Args:
        loc_string (str): Dot-separated string representing a sequence of locations and a departure time (e.g., "A.B.C.12:00").
        weekday (str): The weekday name (e.g., 'Mon') representing the reference date for departure.
        day (str): The actual day of the movement (e.g., 'Mon'). Used to calculate day offsets.
        running_days (list): List of weekday names indicating on which days the movement runs.
        traffictype (str): Type of traffic (e.g., 'Express').
        vehicle (int): Vehicle identifier.
        tu_dest (str): Destination for the transport unit (optional).
        co_con_time (int): Changeover connection time in minutes between legs (default: 15).
        shift_id (int): Identifier for the shift (default: 1).
        dep_day (int): Additional day offset for departure (default: 0).
    Returns:
        list: List of OptMovements records created for the parsed movements. Returns an empty list if no records are created or an error occurs.
    Raises:
        ValueError: If a movement cannot be created for a given leg due to missing or zero runtime.
    Side Effects:
        - Registers new changeovers in LocalChangeOversId if multiple legs are present.
        - Logs exceptions using OPT_LOGGER.
        - Rolls back the database session on SQLAlchemy errors.
    """

    try:

        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        records = []

        if loc_string != '':

            __locs = [x.strip()
                        for x in loc_string.split('.')]

            __deptime = __locs.pop()
            is_multi_leg = len(__locs) > 2

            if is_multi_leg and tu_dest == '':
                tu_dest = __locs[-1]

            __days_offset = 0
            if weekday != day:

                if weekday == 'Sun' and day == 'Mon':
                    __days_offset = 1

                elif weekday == 'Mon' and day == 'Sun':
                    __days_offset = -1
                else:
                    __days_offset = weekdays.index(
                        day) - weekdays.index(weekday)

            dep_dt = combine_date_time(
                LION_DATES[weekday] + timedelta(days=__days_offset + dep_day), __deptime)

            __loc_from = __locs.pop(0)
            __new_movs = []
            __tu_leg = 0

            dct_movements = {}
            dct_ms = {}

            while __locs:

                __tu_leg += 1
                __loc_to = __locs.pop(0)

                __dct_movement = UI_MOVEMENTS.rebuild_movement(
                    m=UI_MOVEMENTS.get_new_loaded_movement_id(),
                    orig=__loc_from,
                    dest=__loc_to,
                    traffic_type=traffictype,
                    tu_loc=tu_dest,
                    loc_string=loc_string,
                    DepDateTime=dep_dt,
                    ArrDateTime=None,
                    vehicle=vehicle,
                    shift=MOVEMENT_DUMP_AREA_NAME if shift_id == 1 else 'N/A',
                    shift_id=shift_id)

                if __dct_movement:

                    __new_movs.append(__dct_movement['MovementID'])

                    dct_ms.update({__tu_leg: __dct_movement['MovementID']})
                    dct_movements.update(
                        {__dct_movement['MovementID']: __dct_movement})

                    if __locs:

                        dep_dt = __dct_movement['ArrDateTime'] + \
                            timedelta(minutes=co_con_time)

                        __loc_from = '%s' % (__loc_to)

                else:
                    raise ValueError(
                        'No movement could be created for %s->%s. Could be due to missing or zero runtime.' % (
                            __loc_from, __loc_to))

            if len(dct_ms) > 1:
                Changeover.register_new(
                    loc_string=loc_string, tu_dest=tu_dest, dct_movements=dct_ms)

            try:
                for m in dct_movements.keys():

                    rcrd = OptMovements(
                        movement_id=dct_movements[m]['MovementID'],
                        str_id=dct_movements[m]['str_id'],
                        loc_string=dct_movements[m]['loc_string'],
                        tu_dest=dct_movements[m]['tu'],
                        mon=int('Mon' in running_days),
                        tue=int('Tue' in running_days),
                        wed=int('Wed' in running_days),
                        thu=int('Thu' in running_days),
                        fri=int('Fri' in running_days),
                        sun=int('Sun' in running_days))

                    records.append(rcrd)

            except SQLAlchemyError as err:
                LION_SQLALCHEMY_DB.session.rollback()
                OPT_LOGGER.log_exception(
                    popup=False, remarks=f'Error when inserting new changeover movements: {str(err)}')

            except Exception:
                LION_SQLALCHEMY_DB.session.rollback()
                OPT_LOGGER.log_exception(
                    popup=False, remarks='Error when inserting new changeover movements')

        return records

    except Exception:
        OPT_LOGGER.log_exception(popup=False)

    return []