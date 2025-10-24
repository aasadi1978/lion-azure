from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.optimization.orm.opt_movements import OptMovements as OptMovements


def transfer_new_movements_to_local_database():
    """
    Transfers all new movement records from the OptMovements table to the LocalMovements table in the local database.
    This function queries all records from the OptMovements table, creates corresponding LocalMovements objects,
    and adds them to the local database. If an error occurs during the database operation, the transaction is rolled back
    and the error is logged.
    Returns:
        bool: True if the transfer was successful, False otherwise.
    """

    OPT_LOGGER.log_statusbar(message='Transferring movements from to LocalMovements table ...')

    try:

        records: list[OptMovements] = OptMovements.query.all()
        list_records = [
            ShiftMovementEntry(
                movement_id=rcrd.movement_id,
                str_id=rcrd.str_id,
                tu_dest=rcrd.tu_dest,
                is_loaded=True,
                shift_id=0
            ) for rcrd in records
        ]

        LION_SQLALCHEMY_DB.session.add_all(list_records)
        LION_SQLALCHEMY_DB.session.commit()
        
    except SQLAlchemyError as err:
        LION_SQLALCHEMY_DB.session.rollback()
        OPT_LOGGER.log_exception(f'Error saving movements to local: {str(err)}')
        return False
    
    except Exception as err:
        LION_SQLALCHEMY_DB.session.rollback()
        OPT_LOGGER.log_exception(f'Error processing movements: {str(err)}')
        return False

    return True