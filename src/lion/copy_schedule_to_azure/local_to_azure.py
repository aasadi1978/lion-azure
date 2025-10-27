import logging
from flask import Flask, g
from sqlalchemy.exc import SQLAlchemyError
from lion.bootstrap.constants import LION_DEFAULT_GROUP_NAME
from lion.create_flask_app.create_app import LION_FLASK_APP, LION_SQLALCHEMY_DB

# --- IMPORTS: LOCAL ORM MODELS ---
from lion.logger.exception_logger import log_exception
from pickle import dumps as pkl_dumps
from lion.orm_local.shift_movement_entry import ShiftMovementEntry as LocalShiftMovementEntry
from lion.orm_local.user_params import UserParams as LocalUserParams
from lion.orm_local.operators import Operator as LocalOperator
from lion.orm_local.vehicle_type import VehicleType as LocalVehicleType
from lion.orm_local.traffic_type import TrafficType as LocalTrafficType
from lion.orm_local.changeover import Changeover as LocalChangeover
from lion.orm_local.drivers_info import DriversInfo as LocalDriversInfo
from lion.orm_local.cost import Cost as LocalCost
from lion.orm_local.orm_runtimes_mileages import RuntimesMileages as LocalRuntimesMileages
from lion.orm_local.location import Location as LocalLocation
from lion.orm_local.resources import Resources as LocalResources
# from lion.orm_local.user import User as LocalUser
from lion.orm_local.groups import GroupName as LocalGroupName
from lion.orm_local.scenarios import Scenarios as LocalScenarios
# --- IMPORTS: AZURE ORM MODELS ---
from lion.orm.shift_movement_entry import ShiftMovementEntry as AzureShiftMovementEntry
from lion.orm.user_params import UserParams as AzureUserParams
from lion.orm.operators import Operator as AzureOperator
from lion.orm.vehicle_type import VehicleType as AzureVehicleType
from lion.orm.traffic_type import TrafficType as AzureTrafficType
from lion.orm.changeover import Changeover as AzureChangeover
from lion.orm.drivers_info import DriversInfo as AzureDriversInfo
from lion.orm.cost import Cost as AzureCost
from lion.orm.orm_runtimes_mileages import RuntimesMileages as AzureRuntimesMileages
from lion.orm.location import Location as AzureLocation
from lion.orm.resources import Resources as AzureResources
# from lion.orm.user import User as AzureUser
from lion.orm.groups import GroupName as AzureGroupName
from lion.orm.scenarios import Scenarios as AzureScenarios

def copy_drivers_info(exclude_fields=None):

    try:

        records = LocalDriversInfo.query.all()
        _list_shift_ids = [shift for shift, in LocalDriversInfo.query.with_entities(LocalDriversInfo.shift_id).all()]

        dct_data = {shftid: LocalDriversInfo.load_shift_data(shiftid=shftid) for shftid in _list_shift_ids}

        updated_records_with_group_name: list[AzureDriversInfo] = []

        for rcrd in records:
            rcrd.group_name = g.get('current_group')
            rcrd.user_id = g.get('current_user_id')
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

            AzureDriversInfo.clear_all()
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


# def copy_user_table():

#     try:

#         records = LocalUser.query.all()
#         if records:
#             # Convert to Azure-compatible instances
#             azure_objects = [
#                 AzureUser(
#                     **{attr: getattr(r, attr)
#                     for attr in r.__dict__
#                     if not attr.startswith('_')}
#                 )
#                 for r in records
#             ]

#             LION_SQLALCHEMY_DB.session.query(AzureUser).delete()
#             LION_SQLALCHEMY_DB.session.commit()

#             LION_SQLALCHEMY_DB.session.bulk_save_objects(azure_objects)
#             LION_SQLALCHEMY_DB.session.commit()

#         return len(AzureUser.query.all()) == len(azure_objects)

#     except SQLAlchemyError as e:
#         log_exception(popup=False, remarks=f"{str(e)}")
#         LION_SQLALCHEMY_DB.session.rollback()

#     except Exception:
#         log_exception(popup=False)
#         LION_SQLALCHEMY_DB.session.rollback()
    
#     finally:
#         LION_SQLALCHEMY_DB.session.close()
#         LION_SQLALCHEMY_DB.engine.dispose()

#     return False

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
                obj.group_name = g.get('current_group')
            if hasattr(obj, 'user_id'):
                obj.user_id = g.get('current_user_id')

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
def start_copy(app: Flask):

    with app.app_context():

        g.current_scn_id = 1  # Default scenario ID for context
        g.current_scn_name = 'demo'
        g.current_group = LION_DEFAULT_GROUP_NAME
        g.current_user_id = 'guest123'

        logging.info("Starting data copy from local ORM to Azure ORM...")

        table_pairs = [
            (LocalShiftMovementEntry, AzureShiftMovementEntry),
            (LocalUserParams, AzureUserParams),
            # (LocalLogEntry, AzureLogEntry),
            (LocalOperator, AzureOperator),
            (LocalVehicleType, AzureVehicleType),
            # (LocalPickleDumps, AzurePickleDumps),
            (LocalTrafficType, AzureTrafficType),
            (LocalChangeover, AzureChangeover),
            (LocalCost, AzureCost),
            (LocalRuntimesMileages, AzureRuntimesMileages),
            # (LocalDriverReport, AzureDriverReport),
            # (LocalLocationMapper, AzureLocationMapper),
            (LocalLocation, AzureLocation),
            # (LocalOptMovements, AzureOptMovements),
            (LocalResources, AzureResources),
            # (LocalTimeStamp, AzureTimeStamp),
            (LocalGroupName, AzureGroupName),
            (LocalScenarios, AzureScenarios),
            # (LocalUser, AzureUser),  # Handled separately due to exclude fields
            # (LocalDriversInfo, AzureDriversInfo), # Handled separately due to data fields (pickle dumps)
        ]

        results = {}
        results['DriversInfo'] = copy_drivers_info()
        # results['User'] = copy_user_table()

        for local_cls, azure_cls in table_pairs:
            try:
                results[local_cls.__name__] = copy_data(local_cls, azure_cls)
            except Exception as e:
                logging.error(f"Error copying data from {local_cls.__name__} to {azure_cls.__name__}: {e}")

        logging.info("Data copy process completed.")
        return results
