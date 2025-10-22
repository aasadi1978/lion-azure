from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.drivers_info import DriversInfo
from lion.shift_data.shift_data import UI_SHIFT_DATA


def to_console():

    try:

        SET_SHIFT_IDS_PER_REP_DAY = set([d for d in OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE
                                        if d in DriversInfo.shift_ids_running_on_weekdays(
                                            weekdays=[OPT_PARAMS.OPTIMIZATION_REP_DAY])])

        n_all_m = len(OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT) + \
            len(OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE)

        num_drivers_to_optimize = len(OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE)
        n_excluded_tours = len(OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT)
        _all_tours = num_drivers_to_optimize + n_excluded_tours


        message = f'Per request from the user, user defined loaded movements will be optimized.'
        message = f'{message}\nPlease note that the excldued tours/movements will be based on'
        message = f'{message} {UI_SHIFT_DATA.scn_name}.'
        OPT_LOGGER.log_info(message=message)

        OPT_LOGGER.log_info(
            message=f'Excluded/incl/total shifts count (scope): {n_excluded_tours}/{num_drivers_to_optimize}/{_all_tours}; ' +
            f'Excl. {OPT_PARAMS.OPTIMIZATION_REP_DAY} data: {len(SET_SHIFT_IDS_PER_REP_DAY)}')

        OPT_LOGGER.log_info(
            message=f'Movements count to optimize (scope): {len(OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE)}/{n_all_m}')

        OPT_LOGGER.log_info(
            message=f'# of tours to be replaced on {';'.join(OPT_PARAMS.OPTIMIZATION_WEEKDAYS)}: {num_drivers_to_optimize}')

        OPT_LOGGER.log_info(
            message=f'# of tours to be replaced on {OPT_PARAMS.OPTIMIZATION_REP_DAY}: {len(SET_SHIFT_IDS_PER_REP_DAY)}')

        OPT_LOGGER.log_info(message=f"Initial tours count: {num_drivers_to_optimize}")

    except Exception as e:
        OPT_LOGGER.log_exception(
            popup=False, remarks=f'Error in log_info: {str(e)}')