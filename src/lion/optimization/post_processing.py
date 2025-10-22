from datetime import datetime
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.scn_info import ScnInfo
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.ui.ui_params import UI_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.elapsed_time import ELAPSED_TIME

def post_processing():

    try:

        logFileMessage = f"Running post processing ... \n Optimization time elapse: {ELAPSED_TIME.collapsed_time()}"
        logFileMessage = f"{logFileMessage}\nProcessing output & generating reprots ..."
        OPT_LOGGER.log_info(message=logFileMessage)

        OPT_PARAMS.EXCLUDED_LOCS = []
        scn_name = ScnInfo.get_param(param='scn_name', if_null='')

        if scn_name:
            scn_name = f'Optimised-{scn_name} - {datetime.now().strftime('%Y%m%d-%H%M')}'
        else:
            scn_name = f"Optimised schedule {datetime.now().strftime('%Y%m%d-%H%M')}"

        OPT_PARAMS.LION_TEMP_OPTIMIZED_SCN_NAME = scn_name

        ScnInfo.update(scn_name=scn_name)
        ScnInfo.delete_param(param='scn_id')

        unplanned = [m for m, in ShiftMovementEntry.query.with_entities(
            ShiftMovementEntry.movement_id).filter(ShiftMovementEntry.shift_id == 0).all()]

        unplanned_long_movs = [
            m for m in unplanned if m in OPT_PARAMS.SETOF_DOUBLEMAN_MOVEMENTS]

        success_message = 'Optimization completed successfully.'

        if unplanned:

            success_message = f'{success_message}: {len(unplanned)} out of {len(OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE)} movements not scheduled'

            if unplanned_long_movs:
                success_message = f'{success_message} out of which {len(unplanned_long_movs)} are more suitable for double man shift!'
                success_message = f'{success_message} Thus the number of unplanned regular movements is: {len(unplanned) - len(unplanned_long_movs)}.'
            else:
                success_message = f'{success_message}.'

        success_message = f'{success_message}\nElapsed time: {
            ELAPSED_TIME.collapsed_time()}'

        OPT_LOGGER.log_info(message=success_message)

        # dump_kpis

        UI_PARAMS.DICT_DRIVERS_PER_PAGE = {}
        UI_MOVEMENTS.reset()
        UI_SHIFT_DATA.reset()

        # if not self.load_movements_object():
        #     OPT_LOGGER.log_info(
        #         message='load_movements_object has failed!')

        return {'success': success_message, 'failure': ''}

    except Exception:

        err = OPT_LOGGER.log_exception(
            popup=False, remarks='Optimization failed!')

        OPT_LOGGER.log_info(message=err)

        return {'failure': err, 'success': ''}
