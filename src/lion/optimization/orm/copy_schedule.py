
from datetime import datetime
import logging
import sqlite3
from lion.bootstrap.constants import LION_TEMP_SCENARIO_DATABASE_NAME
from lion.config.paths import LION_SQLDB_PATH
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.orm.scn_info import ScnInfo
from lion.orm.temp_scn_info import TempScnInfo
from sqlalchemy.exc import SQLAlchemyError
from pickle import dumps as pickle_dumps
from lion.orm.temp_shift_movement_entry import TempShiftMovementEntry
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.drivers_info import DriversInfo
from lion.orm.temp_drivers_info import TempDriversInfo
from lion.orm.temp_changeover import TempChangeover
from lion.orm.changeover import Changeover

timestamp = datetime.now()

def copy_movements():

    try:

        old_records = TempShiftMovementEntry.query.all()
        extend_records = [ShiftMovementEntry(
            **{attr: getattr(rcrd, attr) for attr in rcrd.__dict__ if not attr.startswith('_') and attr not in ['user_id', 'group_name']})
            for rcrd in old_records]

        if extend_records:

            ShiftMovementEntry.clear_all()
            extend_records_updated = []
            for r in extend_records:
                r.group_name = LION_FLASK_APP.config['LION_USER_GROUP_NAME']
                r.user_id = LION_FLASK_APP.config['LION_USER_ID']

                extend_records_updated.append(r)

            LION_SQLALCHEMY_DB.session.bulk_save_objects(extend_records_updated)
            LION_SQLALCHEMY_DB.session.commit()

            ShiftMovementEntry.clean_up_loc_strings()

            return len(ShiftMovementEntry.query.all()) == len(extend_records_updated)

    except SQLAlchemyError as err:
        log_exception(popup=False, remarks=str(err))
        LION_SQLALCHEMY_DB.session.rollback()

    except Exception:
        log_exception(popup=False)
        LION_SQLALCHEMY_DB.session.rollback()

    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()

    return False


def copy_changeovers():

    try:

        records = TempChangeover.query.all()
        extend_records = [Changeover(
            **{attr: getattr(rcrd, attr) for attr in rcrd.__dict__ if not attr.startswith('_') and attr not in ['user', 'user_id', 'group_name']})
            for rcrd in records]

        updated_records = []
        if extend_records:

            for r in extend_records:
                r.group_name = LION_FLASK_APP.config['LION_USER_GROUP_NAME']
                r.user_id = LION_FLASK_APP.config['LION_USER_ID']
                updated_records.append(r)

            Changeover.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

            LION_SQLALCHEMY_DB.session.bulk_save_objects(updated_records)
            LION_SQLALCHEMY_DB.session.commit()

        return len(Changeover.query.all()) == len(extend_records), []

    except SQLAlchemyError as e:
        log_exception(popup=False, remarks=f"{str(e)}")
        LION_SQLALCHEMY_DB.session.rollback()

    except Exception:
        log_exception(popup=False)
        LION_SQLALCHEMY_DB.session.rollback()

    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()

    return False, []

def copy_schedule():

    try:

        records = TempDriversInfo.query.all()
        _list_shift_ids = [shift for shift, in TempDriversInfo.query.with_entities(TempDriversInfo.shift_id).all()]

        dct_data = {shftid: TempDriversInfo.load_shift_data(shiftid=shftid) for shftid in _list_shift_ids}

        updated_records_with_group_name = []
        for rcrd in records:
            rcrd.group_name = LION_FLASK_APP.config['LION_USER_GROUP_NAME']
            rcrd.user_id = LION_FLASK_APP.config['LION_USER_ID']
            updated_records_with_group_name.append(rcrd)

        extend_records = [DriversInfo(
            **{attr: getattr(rcrd, attr) for attr in rcrd.__dict__ if not attr.startswith('_') and attr not in [
                'data', 'timestamp']})
            for rcrd in updated_records_with_group_name]

        if extend_records:

            extend_records_with_data = []
            for rcrd in extend_records:

                setattr(rcrd, 'data', pickle_dumps(dct_data[rcrd.shift_id]))
                rcrd.double_man = rcrd.double_man or dct_data[rcrd.shift_id].get('double_man', False)
                extend_records_with_data.append(rcrd)

            DriversInfo.clear_all()
            LION_SQLALCHEMY_DB.session.bulk_save_objects(extend_records_with_data)
            LION_SQLALCHEMY_DB.session.commit()

        return len(DriversInfo.query.all()) == len(extend_records)

    except SQLAlchemyError as e:
        log_exception(popup=False, remarks=f"{str(e)}")
        LION_SQLALCHEMY_DB.session.rollback()

    except Exception:
        log_exception(popup=False)
        LION_SQLALCHEMY_DB.session.rollback()
    
    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()

    return False

def copy_scn_info():

    try:

        records = TempScnInfo.query.all()
        extend_records = [ScnInfo(
            **{attr: getattr(rcrd, attr) for attr in rcrd.__dict__ if not attr.startswith('_')})
            for rcrd in records]

        if extend_records:

            ScnInfo.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

            LION_SQLALCHEMY_DB.session.bulk_save_objects(extend_records)
            LION_SQLALCHEMY_DB.session.commit()

        return len(ScnInfo.query.all()) == len(extend_records)

    except SQLAlchemyError as e:
        log_exception(popup=False, remarks=f"{str(e)}")
        LION_SQLALCHEMY_DB.session.rollback()

    except Exception:
        log_exception(popup=False)
        LION_SQLALCHEMY_DB.session.rollback()

    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()

    return False

def copy_schedule_data():

    """
    This module copies schedule data from external schedule tables to the local database, i.e., updates local_schedule.db.
    The module updates the group name and user ID for all copied records based on the current user's information.
    """
    try:

        co_copied = copy_changeovers()
        shifts_copied = copy_schedule()
        movements_copied = copy_movements()
        scn_info_copied = copy_scn_info()

        status = movements_copied and shifts_copied and co_copied and scn_info_copied

        return status

    except Exception:
        log_exception(
            popup=False, remarks='Schedule could not be copied!')

        return False