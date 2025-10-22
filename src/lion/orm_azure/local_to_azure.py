import logging
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.create_app import LION_FLASK_APP, LION_SQLALCHEMY_DB

# --- IMPORTS: LOCAL ORM MODELS ---
from lion.logger.exception_logger import log_exception
from pickle import dumps as pkl_dumps
from lion.orm.shift_movement_entry import ShiftMovementEntry as LocalShiftMovementEntry
from lion.orm.user_params import UserParams as LocalUserParams
from lion.logger.log_entry import LogEntry as LocalLogEntry
from lion.orm.operators import Operator as LocalOperator
from lion.orm.vehicle_type import VehicleType as LocalVehicleType
from lion.orm.pickle_dumps import PickleDumps as LocalPickleDumps
from lion.orm.traffic_type import TrafficType as LocalTrafficType
from lion.orm.changeover import Changeover as LocalChangeover
from lion.orm.drivers_info import DriversInfo as LocalDriversInfo
from lion.orm.cost import Cost as LocalCost
from lion.runtimes.orm_runtimes_mileages import RuntimesMileages as LocalRuntimesMileages
from lion.orm.driver_report import DriverReport as LocalDriverReport
from lion.orm.location_mapping import LocationMapper as LocalLocationMapper
from lion.orm.location import Location as LocalLocation
from lion.orm.opt_movements import OptMovements as LocalOptMovements
from lion.orm.resources import Resources as LocalResources
from lion.orm.time_stamp import TimeStamp as LocalTimeStamp
from lion.orm.user import User as LocalUser
from lion.orm.groups import GroupName as LocalGroupName

# --- IMPORTS: AZURE ORM MODELS ---
from lion.orm_azure.shift_movement_entry import ShiftMovementEntry as AzureShiftMovementEntry
from lion.orm_azure.user_params import UserParams as AzureUserParams
from lion.orm_azure.log_entry import LogEntry as AzureLogEntry
from lion.orm_azure.operators import Operator as AzureOperator
from lion.orm_azure.vehicle_type import VehicleType as AzureVehicleType
from lion.orm_azure.pickle_dumps import PickleDumps as AzurePickleDumps
from lion.orm_azure.traffic_type import TrafficType as AzureTrafficType
from lion.orm_azure.changeover import Changeover as AzureChangeover
from lion.orm_azure.drivers_info import DriversInfo as AzureDriversInfo
from lion.orm_azure.cost import Cost as AzureCost
from lion.orm_azure.orm_runtimes_mileages import RuntimesMileages as AzureRuntimesMileages
from lion.orm_azure.driver_report import DriverReport as AzureDriverReport
from lion.orm_azure.location_mapping import LocationMapper as AzureLocationMapper
from lion.orm_azure.location import Location as AzureLocation
from lion.orm_azure.opt_movements import OptMovements as AzureOptMovements
from lion.orm_azure.resources import Resources as AzureResources
from lion.orm_azure.time_stamp import TimeStamp as AzureTimeStamp
from lion.orm_azure.user import User as AzureUser
from lion.orm_azure.groups import GroupName as AzureGroupName

def copy_drivers_info(exclude_fields=None):

    try:

        records = LocalDriversInfo.query.all()
        _list_shift_ids = [shift for shift, in LocalDriversInfo.query.with_entities(LocalDriversInfo.shift_id).all()]

        dct_data = {shftid: LocalDriversInfo.load_shift_data(shiftid=shftid) for shftid in _list_shift_ids}

        updated_records_with_group_name = []
        for rcrd in records:
            rcrd.group_name = LION_FLASK_APP.config['LION_USER_GROUP_NAME']
            rcrd.user_id = LION_FLASK_APP.config['LION_USER_ID']
            updated_records_with_group_name.append(rcrd)

        extend_records = [AzureDriversInfo(
            **{attr: getattr(rcrd, attr) for attr in rcrd.__dict__ if not attr.startswith('_') and attr not in [
                'data', 'timestamp']})
            for rcrd in updated_records_with_group_name]

        if extend_records:

            extend_records_with_data = []
            for rcrd in extend_records:

                setattr(rcrd, 'data', pkl_dumps(dct_data[rcrd.shift_id]))
                rcrd.double_man = rcrd.double_man or dct_data[rcrd.shift_id].get('double_man', False)
                extend_records_with_data.append(rcrd)

            LION_SQLALCHEMY_DB.session.query(AzureDriversInfo).delete()
            LION_SQLALCHEMY_DB.session.commit()

            LION_SQLALCHEMY_DB.session.bulk_save_objects(extend_records_with_data)
            LION_SQLALCHEMY_DB.session.commit()

        return len(AzureDriversInfo.query.all()) == len(extend_records)

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


def copy_user_table():

    try:

        records = LocalUser.query.all()
        if records:
            # Convert to Azure-compatible instances
            azure_objects = [
                AzureUser(
                    **{attr: getattr(r, attr)
                    for attr in r.__dict__
                    if not attr.startswith('_')}
                )
                for r in records
            ]

            LION_SQLALCHEMY_DB.session.query(AzureUser).delete()
            LION_SQLALCHEMY_DB.session.commit()

            LION_SQLALCHEMY_DB.session.bulk_save_objects(azure_objects)
            LION_SQLALCHEMY_DB.session.commit()

        return len(AzureUser.query.all()) == len(azure_objects)

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

# --- GENERIC COPY FUNCTION ---
def copy_data(local_cls, azure_cls, exclude_fields=None):
    
    logging.info(f"Copying data from {local_cls.__name__} to {azure_cls.__name__}...")

    exclude_fields = exclude_fields or ['user_id', 'group_name', 'object_id']

    try:
        old_records = local_cls.query.all()
        if not old_records:
            logging.info(f"No records found in {local_cls.__name__}")
            return False

        # Convert to Azure-compatible instances
        azure_objects = [
            azure_cls(
                **{attr: getattr(r, attr)
                   for attr in r.__dict__
                   if not attr.startswith('_') and attr not in exclude_fields}
            )
            for r in old_records
        ]

        # Clear existing Azure table if available
        if hasattr(azure_cls, 'clear_all'):
            azure_cls.clear_all()
        else:
            LION_SQLALCHEMY_DB.session.query(azure_cls).delete()
            LION_SQLALCHEMY_DB.session.commit()

        # Add user/group metadata if applicable
        for obj in azure_objects:
            if hasattr(obj, 'group_name'):
                obj.group_name = LION_FLASK_APP.config.get('LION_USER_GROUP_NAME')
            if hasattr(obj, 'user_id'):
                obj.user_id = LION_FLASK_APP.config.get('LION_USER_ID')
            if hasattr(obj, 'object_id'):
                obj.object_id = LION_FLASK_APP.config.get('LION_OBJECT_ID')

        # Bulk insert
        LION_SQLALCHEMY_DB.session.bulk_save_objects(azure_objects)
        LION_SQLALCHEMY_DB.session.commit()

        # Optional cleanup methods
        for fn in ['clean_up_loc_strings', 'cleanup_records', 'post_sync']:
            if hasattr(azure_cls, fn):
                getattr(azure_cls, fn)()

        logging.info(f"{local_cls.__name__} → {azure_cls.__name__} copied successfully ({len(azure_objects)} records).")
        return True

    except SQLAlchemyError as err:
        log_exception(popup=False, remarks=f"{local_cls.__name__}: {err}")
        LION_SQLALCHEMY_DB.session.rollback()

    except Exception as e:
        log_exception(popup=False, remarks=f"{local_cls.__name__}: {e}")
        LION_SQLALCHEMY_DB.session.rollback()

    finally:
        LION_SQLALCHEMY_DB.session.close()
        LION_SQLALCHEMY_DB.engine.dispose()

    input("Press Enter to continue...")
    return False


# --- MAIN FUNCTION TO APPLY COPY TO ALL PAIRS ---
def copy_data_to_azure(app: Flask):

    with app.app_context():

        logging.info("Starting data copy from local ORM to Azure ORM...")
        table_pairs = [
            (LocalShiftMovementEntry, AzureShiftMovementEntry),
            (LocalUserParams, AzureUserParams),
            (LocalLogEntry, AzureLogEntry),
            (LocalOperator, AzureOperator),
            (LocalVehicleType, AzureVehicleType),
            (LocalPickleDumps, AzurePickleDumps),
            (LocalTrafficType, AzureTrafficType),
            (LocalChangeover, AzureChangeover),
            (LocalCost, AzureCost),
            (LocalRuntimesMileages, AzureRuntimesMileages),
            (LocalDriverReport, AzureDriverReport),
            (LocalLocationMapper, AzureLocationMapper),
            (LocalLocation, AzureLocation),
            (LocalOptMovements, AzureOptMovements),
            (LocalResources, AzureResources),
            (LocalTimeStamp, AzureTimeStamp),
            (LocalGroupName, AzureGroupName),
            # (LocalUser, AzureUser),  # Handled separately due to exclude fields
            # (LocalDriversInfo, AzureDriversInfo), # Handled separately due to data fields (pickle dumps)
        ]

        results = {}
        results['DriversInfo'] = copy_drivers_info()
        results['User'] = copy_user_table()

        for local_cls, azure_cls in table_pairs:
            try:
                results[local_cls.__name__] = copy_data(local_cls, azure_cls)
            except Exception as e:
                logging.error(f"Error copying data from {local_cls.__name__} to {azure_cls.__name__}: {e}")

        logging.info("Data copy process completed.")
        return results
