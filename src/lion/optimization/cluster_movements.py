from collections import defaultdict

from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER


def cluster_movements():

    dct_recommended_movements_per_driver_loc = defaultdict(set)
    set_movements_with_no_recom = set()

    dct_driver_locs_per_lane = OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE
    dict_movements_to_optimize = OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE

    if dct_driver_locs_per_lane:

        set_recommended_driver_loc = set()
        errors = ''

        for mv in set(dict_movements_to_optimize):

            loc_from = dict_movements_to_optimize[mv]['From']
            locTo = dict_movements_to_optimize[mv]['To']

            try:
                lhid = '.'.join(
                    [loc_from, locTo,
                        dict_movements_to_optimize[mv]['DepDateTime'].strftime('%H%M')])

                lane = '.'.join([loc_from, locTo])

                set_recommended_driver_loc = dct_driver_locs_per_lane.get(
                    lhid, dct_driver_locs_per_lane.get(lane, dct_driver_locs_per_lane.get(loc_from, set())))

                if set_recommended_driver_loc:
                    [dct_recommended_movements_per_driver_loc[loccode].update([mv])
                        for loccode in set_recommended_driver_loc]
                else:
                    set_movements_with_no_recom.add(mv)

            except Exception as e:
                err = f'Could not recommend any driver loc to {mv}: {str(e)}'
                errors = f"{errors}{err}\n"

        if errors != '':
            errors = f"Error occured when recommending driver loc:\n{
                errors}"
            OPT_LOGGER.log_exception(message=errors)

        del errors, set_recommended_driver_loc

    return dct_recommended_movements_per_driver_loc, set_movements_with_no_recom