# At module level (top of build_schedule.py)
from pickle import loads as pickle_loads, UnpicklingError
import logging

from lion.tour.dct_tour import DctTour

def transform_shift_record(shiftObj) -> tuple[int, DctTour, dict] | None:
    try:

        dct_tour_base = {}
        try:
            dct_tour_base = pickle_loads(shiftObj.data)
        except UnpicklingError as err:
            logging.warning(f"Safe error: {err}")
            return None
        except Exception as e:
            logging.error(f"Error unpickling shift data for {shiftObj.shiftname}: {e}")
            return None
        
        if not dct_tour_base:
            logging.warning(f"Empty shift for {shiftObj.shiftname}")
            return None

        dct_tour_base = DctTour(**dct_tour_base)
        dct_tour_base.shift_id = shiftObj.shift_id
        dct_tour_base.shiftname = shiftObj.shiftname

        return shiftObj.shift_id, dct_tour_base, {
            m: shiftObj.shift_id for m in dct_tour_base.list_movements
        }

    except Exception as e:
        logging.error(f"Error building shift {shiftObj.shiftname or 'unknown'}: {e}")
        return None
