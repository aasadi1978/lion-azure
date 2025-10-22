import logging
from os import remove
from lion.config.paths import LION_LOGS_PATH
from lion.logger.exception_logger import log_exception
from lion.logger.status_logger import log_message
from lion.orm.changeover import Changeover
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.ui.ui_params import UI_PARAMS


def confirm(entry_movs=[], linked_movs=[]):

    try:

        if not linked_movs:
            linked_movs = [m for m , in Changeover.query.with_entities(Changeover.movement_id).all()]

        if not entry_movs:
            entry_movs = [m for m, in ShiftMovementEntry.query.with_entities(ShiftMovementEntry.movement_id).all()]

        if not linked_movs:
            raise ValueError('No changeovers found!')
        
        missing_movs = [m for m in linked_movs if m not in entry_movs]

        if not missing_movs:

            loc_strings = set([locstr for locstr, in Changeover.query.filter(
                Changeover.movement_id.in_(missing_movs)).all()])
            
            UI_PARAMS.CHANGEOVERS_VALIDATED = True

            log_message(f"There are {len(loc_strings)} valid changeovers.")

    except Exception:
        log_exception(popup=False, remarks=f"Could not confirm changeover repairs. ")
        UI_PARAMS.CHANGEOVERS_VALIDATED = False


def validate_changeovers():

    logging.info("Validating changeovers ...")
    log_file_path = LION_LOGS_PATH / 'invalid_changeovers.csv'
    if log_file_path.exists():
        remove(log_file_path)

    if UI_PARAMS.CHANGEOVERS_VALIDATED:
        return

    try:
        linked_movs = [m for m, in Changeover.query.with_entities(Changeover.movement_id).all()]
        entry_movs = [m for m, in ShiftMovementEntry.query.with_entities(ShiftMovementEntry.movement_id).all()]
        missing_movs = [m for m in linked_movs if m not in entry_movs]

    except Exception as e:
        logging.error(f"Could not initialize changeover validation. {str(e)}")
        missing_movs = []

    if missing_movs:

        loc_strings = set([locstr for locstr, in Changeover.query.with_entities(
            Changeover.loc_string).filter(Changeover.movement_id.in_(missing_movs)).all()])

        with open(log_file_path, 'w') as f:
            f.writelines(f"{locstr}\n" for locstr in loc_strings)
        
        if not Changeover.delete_changeovers(loc_string=loc_strings):
            logging.error("Could not delete invalid changeovers.")
            return

    else:
        UI_PARAMS.CHANGEOVERS_VALIDATED = True

