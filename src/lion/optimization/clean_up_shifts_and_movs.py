from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry


def clean_up_redundant_shifts_and_movements():
    """
    Cleans up redundant shifts and associated movements within the current optimization scope.
    This function performs the following steps:
    1. Disables the running days for shift IDs specified in the optimization parameters.
    2. Identifies and deletes unused shifts, ensuring only those within the current scope are affected.
    3. Logs any shift IDs marked for deletion that are outside the current scope.
    4. Deletes movements associated with the deleted shift IDs.
    5. Handles and logs any exceptions that occur during the cleanup process.
    Raises:
        Logs exceptions encountered during the cleanup process without raising them further.
    """

    OPT_LOGGER.log_statusbar('Cleaning up out-of-scope shifts and associated movements ...')

    if OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE:

        try:

            DriversInfo.disable_shiftids_running_days(
                shift_ids=OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE,
                weekdays=OPT_PARAMS.OPTIMIZATION_WEEKDAYS,
                logger=OPT_LOGGER
            )

            shifts2del = DriversInfo.clean_up_unused_shifts()
            shifts2del_outofScope = [
                        d for d in shifts2del if d not in OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE]

            if shifts2del_outofScope:
                OPT_LOGGER.log_info(
                            f'These shift ids labeled to be deleted but they are out of scope: {shifts2del_outofScope}')

                shifts2del = [d for d in shifts2del 
                              if d in OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE]

            ShiftMovementEntry.delete_movements_by_shift_ids(
                shift_ids=shifts2del,
                logger=OPT_LOGGER
            )


        except Exception as e:
            OPT_LOGGER.log_exception(
                popup=False, remarks=f"Error during cleanup: {str(e)}")