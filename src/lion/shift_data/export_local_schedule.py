from datetime import datetime
from os import remove
from pathlib import Path
from shutil import copyfile
from lion.bootstrap.constants import LION_SCHEDULE_DATABASE_NAME
from lion.config.paths import LION_SHARED_SCHEDULE_PATH, LION_SQLDB_PATH
from lion.logger.status_logger import log_message
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.scn_info import ScnInfo
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.shift_data.refreshshift import evaluate_shift
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.clean_filename import clean_file_name
from lion.logger.exception_logger import log_exception
from lion.utils.safe_copy import secure_copy
from lion.utils.split_string import split_string
from lion.maintenance.vacuum_db import compress_db_storage

from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB

def export_schedule(**dct_params):

    _status_message = ''

    try:

        scn_name = dct_params.get('scn_name', '')
        scn_note = dct_params.get('scn_note', '')
        pwd = dct_params.get('pwd', '')

        scn_name = clean_file_name(filename=scn_name)

        if not scn_name:

            scn_name = UI_SHIFT_DATA.scn_name
            scn_name = scn_name.split(' by ')[0]
            scn_name = scn_name.replace('Master plan ', '')

        ScnInfo.update(scn_name=scn_name)

        scn_document = ScnInfo.get_param(param='docs', if_null='')

        if scn_note != '':

            hashtag_line = '-' * 50
            _now2 = datetime.now().strftime('%a %b %d AT %H:%M')

            scn_doc_header = f"When: {_now2}"
            scn_doc_header = f"{scn_doc_header} | When: {_now2}"
            scn_doc_header = f"{scn_doc_header} | Who: {LION_FLASK_APP.config['LION_USER_FULL_NAME']}"
            scn_doc_header = f"{scn_doc_header} | ScheduleName: {scn_name}"

            scn_note = split_string(txt=scn_note, line_length=120)
            scn_note = f'{scn_doc_header}\n{scn_note}\n{hashtag_line}\n'

            if scn_document != '':
                scn_document = f"{scn_note}{scn_document}"[:10000]
            else:
                scn_document = f"{scn_note}"
            
            ScnInfo.update(docs=scn_document)

        if (pwd_fld := ScnInfo.query.filter(
            ScnInfo.param == 'password').first()): # type: ignore
            LION_SQLALCHEMY_DB.session.delete(pwd_fld)
            LION_SQLALCHEMY_DB.session.commit()

        is_encrypted = False
        if pwd != '':
            if pwd.lower().strip() != 'public':
                is_encrypted = True
                ScnInfo.set_password(password=pwd.strip())

        if is_encrypted:
            scn_name = f"Encrypted-{scn_name}"
        else:
            if scn_name.startswith('Encrypted-'):
                scn_name = scn_name.replace('Encrypted-', '')

        # Collect all movement ids used in tours in schedule
        # this is to make sure we do not publish unused movs

        dct_missing_used_movements = secure_copy(UI_SHIFT_DATA.dct_missing_used_movements)
        if dct_missing_used_movements:

            for shift_id in dct_missing_used_movements:

                if not shift_id:
                    log_message(f"Refreshing {shift_id} was skipped!")
                    continue

                elif not evaluate_shift(shift_id=shift_id):
                    log_message(f"Refreshing {shift_id} failed!")
                else:
                    log_message(f"Refreshing {shift_id} was successful!")

        _set_all_used_movs = UI_SHIFT_DATA.set_used_movements
        _excpmsg = UI_SHIFT_DATA.exception_message

        if _excpmsg != '':
            log_message(f"{_excpmsg}")

        all_mov_ids = [m for m, in ShiftMovementEntry.query.with_entities(ShiftMovementEntry.movement_id).all()]
        set_unused_movs = set(all_mov_ids) - set(_set_all_used_movs)

        if set_unused_movs:
            ShiftMovementEntry.query.filter(
                ShiftMovementEntry.movement_id.in_(set_unused_movs)).delete()
            LION_SQLALCHEMY_DB.session.commit()

    except Exception:
        __message = log_exception(
            popup=False, remarks='Exporting failed!')

        _status_message = f"{_status_message}. {__message}"


    if not _status_message:

        """
        Create a copy with a new name
        vaccum the database
        copy the vaccumed db to the sahred directory
        delete a temp copy
        """

        try:

            db_local_copy = Path(LION_SQLDB_PATH) / f"{scn_name}.db"

            if Path(db_local_copy).exists():
                try:
                    remove(db_local_copy)
                except:
                    pass
                
            copyfile(src=Path(LION_SQLDB_PATH) / LION_SCHEDULE_DATABASE_NAME, dst=db_local_copy)
            compress_db_storage(db_paths=[db_local_copy])

            dst_path = Path(LION_SHARED_SCHEDULE_PATH) / f"{scn_name}.db"

            copyfile(src=db_local_copy, dst=dst_path)

            if Path(dst_path).exists():
                try:
                    remove(db_local_copy)
                except:
                    pass
                    
                UI_SHIFT_DATA.scn_name = scn_name
                return {'message': f'Schedule has been successfully exported!', 
                        'code': 200}

        except Exception:
            __message = log_exception(
                popup=False, remarks='Exporting failed!')

            _status_message = f"{_status_message}. {__message}"

    return {'message': f'{_status_message}', 
            'code': 400}
