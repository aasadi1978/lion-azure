from datetime import timedelta
import logging
from lion.bootstrap.constants import WEEKDAYS, LOC_STRING_SEPERATOR, LION_DATES, MOVEMENT_DUMP_AREA_NAME
from lion.orm.changeover import Changeover
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.combine_date_time import combine_date_time

def generate_movements_from_loc_string(loc_string,
                                        day='Mon',
                                        traffictype='Express',
                                        vehicle=1,
                                        tu_dest='',
                                        co_con_time=[15]) -> list:

        if not co_con_time:
            co_con_time = [15]
        
        buffr_time = co_con_time[-1]

        def _get_buffer_time(tu_leg):
            try:
                return co_con_time[tu_leg]
            except:
                return buffr_time

        try:

            loc_codes = [x.strip() for x in loc_string.split(LOC_STRING_SEPERATOR)]
            departure_time = loc_codes.pop()

            if len(loc_codes) > 2 and tu_dest == '':
                tu_dest = loc_codes[-1]

            days_offset = 0
            if UI_SHIFT_DATA.weekday != day:

                if UI_SHIFT_DATA.weekday == 'Sun' and day == 'Mon':
                    days_offset = 1

                elif UI_SHIFT_DATA.weekday == 'Mon' and day == 'Sun':
                    days_offset = -1
                else:
                    days_offset = WEEKDAYS.index(day) - WEEKDAYS.index(UI_SHIFT_DATA.weekday)

            dep_dt = combine_date_time(
                LION_DATES[UI_SHIFT_DATA.weekday] + timedelta(days=days_offset), departure_time)

            origin = loc_codes.pop(0)
            list_new_movements = []
            leg_index = 0

            UI_MOVEMENTS.shift = MOVEMENT_DUMP_AREA_NAME
            UI_MOVEMENTS.shift_id = 1

            dct_movements = {}
            dct_ms = {}

            while loc_codes:

                bfr_time = _get_buffer_time(leg_index)
                leg_index += 1
                next_loc = loc_codes.pop(0)

                dct_movement = UI_MOVEMENTS.get_dct_adhoc_movement(
                    orig=origin,
                    dest=next_loc,
                    traffic_type=traffictype,
                    tu_loc=tu_dest,
                    loc_string=loc_string,
                    DepDateTime=dep_dt,
                    ArrDateTime=None,
                    vehicle=vehicle,
                    shift=MOVEMENT_DUMP_AREA_NAME,
                    shift_id=1)

                if dct_movement:

                    list_new_movements.append(dct_movement['MovementID'])

                    dct_ms.update({leg_index: dct_movement['MovementID']})
                    dct_movements.update(
                        {dct_movement['MovementID']: dct_movement})

                    if loc_codes:

                        dep_dt = dct_movement['ArrDateTime'] + timedelta(minutes=bfr_time)
                        origin = f"{next_loc}"

                else:
                    raise ValueError(
                        f'No movement could be created for {origin}->{next_loc}. Could be due to missing or zero runtime.')

            if len(dct_ms) > 1:
                Changeover.register_new(
                    loc_string=loc_string, tu_dest=tu_dest, dct_movements=dct_ms)

            UI_SHIFT_DATA.update(dict_movements=dct_movements)
            return list_new_movements

        except Exception as e:
            logging.critical(f"Error in locstring2movements for {loc_string}: {str(e)}")

        return []