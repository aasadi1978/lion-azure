from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import List
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
import lion.logger.exception_logger as exc_logger
from lion.bootstrap.constants import LION_DATES, MIN_REPOS_MOVEMENT_ID, INIT_LOADED_MOV_ID, MOVEMENT_DUMP_AREA_NAME, RECYCLE_BIN_NAME
from lion.movement.dct_movement import DictMovement
from lion.orm.drivers_info import DriversInfo
from lion.orm.user_params import UserParams
from lion.logger.status_logger import log_message
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.ui.ui_params import UI_PARAMS
from lion.utils import dict2class


class ShiftMovementEntry(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'local_data_bind'
    __tablename__ = 'movements'

    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    extended_str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='')
    str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')
    is_loaded = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)

    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True, default=0)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default='')
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='')

    def __init__(self, **attrs):

        super().__init__(**attrs)

        self.str_id = attrs.get('str_id', '')
        self.shift_id = attrs.get('shift_id', 0)

        is_repos = self.str_id.lower().endswith(
            '|empty') or '|empty|' in self.str_id.lower()

        self.movement_id = attrs.get('movement_id', 0)
        self.is_loaded = not is_repos
        self.loc_string = attrs.get('loc_string', '')
        self.tu_dest = attrs.get('tu_dest', '')
        self.group_name = attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME'])
        self.user_id = attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID'])
        self.extended_str_id = attrs.get('extended_str_id', f"{attrs.get('str_id', '')}|{self.movement_id}")

    @property
    def shift_ids(cls):

        try:
            return list(set([shiftid for shiftid, in cls.query.with_entities(
                cls.shift_id).filter(cls.shift_id > 0).all()]))
        except Exception as e:
            logging.error(f'shift_ids failed! {e}')
            return []

    @classmethod
    def all_movement_objects(cls) -> list:
        try:
            return cls.query.filter(cls.shift_id.isnot(None)).all()
        except Exception as e:
            logging.error(f'movement_objects failed! {e}')
            return []

    @classmethod
    def all_unplanned_movement_ids(cls) -> List[int]:
        try:
            return [m for m, in cls.query.with_entities(cls.movement_id).filter(
                and_(cls.is_loaded, cls.shift_id == 0)).all()]
        except Exception as e:
            logging.error(f'all_unplanned_movement_ids failed! {e}')
            return []

    @classmethod
    def is_changeover(cls, loc_string):

        try:
            return len(loc_string.split('.')) > 3
        except Exception:
            return False

    @classmethod
    def get_movement_ids(cls, loc_string='') -> list:
        try:
            return [obj.movement_id for obj in cls.query.filter(cls.loc_string == loc_string).all()]
        except Exception:
            exc_logger.log_exception(popup=False)
        return []

    @classmethod
    def get_weekday_records(cls, weekday=''):

        try:
            return [obj for obj in cls.query.all()
                    if getattr(obj, weekday.lower(), False)]

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return []

        except Exception:
            exc_logger.log_exception(
                popup=True, remarks='Could not get list of str_ids.')

            LION_SQLALCHEMY_DB.session.rollback()

        return []

    @classmethod
    def update_movement_shift_ids(cls, dct_movement_shift_id=None):
        if not dct_movement_shift_id:
            return

        try:
            # Get relevant objects with only needed columns for efficiency
            objs = cls.query.filter(
                cls.movement_id.in_(dct_movement_shift_id.keys())).all()

            for obj in objs:
                obj.shift_id = dct_movement_shift_id[obj.movement_id]

            LION_SQLALCHEMY_DB.session.bulk_save_objects(objs)
            LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            exc_logger.log_exception(
                popup=True, remarks=f"Error: Could not update shift_ids. {err}")
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def loc_strings(cls):
        """
        returns {'loc_string': [1234, 4567]}
        """

        try:

            return [lcstr for lcstr, in cls.query.with_entities(
                cls.loc_string).filter(cls.loc_string != '').all()]

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            exc_logger.log_exception(
                popup=True, remarks=f"Error: Could not return list_changeovers. {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        return []

    @ classmethod
    def changeover_shift_ids(cls, loc_string=''):
        """
        return list like [1234, 3456]
        """

        try:

            return [obj[0] for obj in
                    cls.query.with_entities(cls.shift_id).filter(cls.loc_string == loc_string)]

        except SQLAlchemyError as e:
            exc_logger.log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return []

    @ classmethod
    def movement_shift_id(cls, movementid):
        """
        return list like [1234, 3456]
        """

        try:

            return [obj[0] for obj in
                    cls.query.with_entities(cls.shift_id).filter(cls.movement_id == movementid)]

        except SQLAlchemyError as e:
            exc_logger.log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return []

    @ classmethod
    def shiftname_changeover_map(cls, weekday=''):

        if weekday == '':
            weekday = UserParams.get_param(
                param='active_weekday', if_null='Mon')

        try:
            return {obj.str_id.split('|')[0]: obj.loc_string for obj in cls.query.all(
            ) if cls.is_changeover(obj.loc_string) and getattr(obj, weekday.lower(), False)}

        # except SQLAlchemyError:
        except Exception:
            exc_logger.log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return {}

    @classmethod
    def changeover_movements(cls, loc_string=''):

        try:
            if loc_string != '':
                return [obj.movement_id for obj in cls.query.all(
                ) if obj.loc_string == loc_string]

        except Exception:
            exc_logger.log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return []

    @classmethod
    def update_mov_str_id(cls, movement_id=0, new_str_id=''):
        """
        This module updates string id of an existing movement.
        A use case can be a new movement created in the dump area and
        after assiging to a shift, str_id has to be updated
        """

        if not movement_id or new_str_id == '':
            return

        try:

            obj_to_update = cls.query.filter_by(
                movement_id=movement_id).first()

            if not obj_to_update:
                raise ValueError(f"The specified movement not found!")

            obj_to_update.str_id = new_str_id
            LION_SQLALCHEMY_DB.session.commit()

            updatedObj = cls.query.filter_by(
                movement_id=movement_id).first()
            if updatedObj.str_id != new_str_id:
                raise ValueError(f"The movement str_id not updated!")

        except Exception:
            exc_logger.log_exception(popup=True,
                           remarks=f'add_str_id failed for {new_str_id}!')

            LION_SQLALCHEMY_DB.session.rollback()

    @ classmethod
    def get_movement_info(cls, str_id=''):
        """
        returns full week mov info
        """

        try:

            obj = cls.query.filter_by(str_id=str_id).first()
            if obj is not None:
                return obj

            is_repos = str_id.lower().endswith('|empty') or '|empty|' in str_id.lower()

            new_obj = cls(
                str_id=str_id,
                movement_id=cls.create_new_digital_id(locstring=str_id),
                is_loaded=not is_repos
            )

            LION_SQLALCHEMY_DB.session.add(new_obj)
            LION_SQLALCHEMY_DB.session.commit()

            obj = cls.query.filter_by(str_id=str_id).first()

            if obj is not None:
                return obj

        except Exception:
            exc_logger.log_exception(popup=True,
                           remarks=f'get_movement_info failed for {str_id}!')

            LION_SQLALCHEMY_DB.session.rollback()

        return None

    @ classmethod
    def add_dct_m(cls, dct_m: dict | DictMovement = {}) -> int:
        """

        Note: dct_m must be DictMovement type
        creates a new records if missing. Specify running days, otherwise, default
        setting will be used, i.e., mon-fri; If record exists, it updates data accordingly
        """

        try:
            if isinstance(dct_m, dict):
                dct_m = DictMovement(**dct_m)

            movement_id = dct_m.get('MovementID', 0)

            if movement_id: 

                record: ShiftMovementEntry = cls.query.filter(
                    and_(cls.str_id == dct_m['str_id'],
                        cls.movement_id == movement_id)).first()

                if record:

                    loc_str: str = dct_m.get('loc_string', '')
                    locs: list = loc_str.split('.')[:-1] if loc_str else []

                    is_changeover = cls.is_changeover(loc_str)
                    tu_dest = locs.pop() if locs else ''

                    record.movement_id = movement_id
                    record.extended_str_id = dct_m.extended_str_id
                    record.str_id = dct_m.str_id
                    record.loc_string = loc_str if is_changeover else ''
                    record.tu_dest = tu_dest
                    record.shift_id = dct_m.shift_id

                    LION_SQLALCHEMY_DB.session.commit()
                    return 1

            movement_id = movement_id or cls.create_new_digital_id(locstring=dct_m.str_id)

            loc_str: str = dct_m.get('loc_string', '')
            is_changeover = cls.is_changeover(loc_str)
            tu_dest = ''

            if is_changeover:

                locs: list = loc_str.split('.')[:-1]
                tu_dest = locs.pop()

            is_repos = dct_m.str_id.lower().endswith('|empty') or '|empty|' in dct_m.str_id.lower()

            record = cls(str_id=dct_m.str_id,
                        movement_id=movement_id,
                        is_loaded=not is_repos,
                        loc_string=loc_str if is_changeover else '',
                        tu_dest=tu_dest)

            record.shift_id = dct_m.shift_id
            LION_SQLALCHEMY_DB.session.add(record)
            LION_SQLALCHEMY_DB.session.commit()

            return movement_id

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False,
                           remarks=f"databse error: get_movement_info {dct_m['str_id']}!: {str(err)}")

            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            exc_logger.log_exception(popup=False,
                           remarks=f"get_movement_info failed for {dct_m['str_id']}!")

            LION_SQLALCHEMY_DB.session.rollback()

        return 0

    @ classmethod
    def update_movement_info(cls, dct_m: DictMovement | dict):
        """
        Note: dct_m must be DictMovement type
        Updates information of an existing movement using digital movement id.
        Running days will not be changed
        """

        try:

            if isinstance(dct_m, dict):
                dct_m = DictMovement(**dct_m)

            record: list[ShiftMovementEntry] = cls.query.filter(
                cls.movement_id == dct_m['MovementID']).first()

            if record:

                record.extended_str_id = dct_m.extended_str_id
                record.str_id = dct_m['str_id']
                # record.loc_string = dct_m['loc_string']
                record.tu_dest = dct_m['tu']
                record.shift_id = dct_m['shift_id']

                LION_SQLALCHEMY_DB.session.commit()

                return True

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=True,
                           remarks=f"updating movement info was not successfull. db error: {str(err)}")

            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            exc_logger.log_exception(popup=True,
                           remarks=f"updating movement info was not successfull. No record was found!")

            LION_SQLALCHEMY_DB.session.rollback()

        return False

    @ classmethod
    def set_weekday_running_status(cls, str_id='', weekday=''):
        """
            This module sets a movement to run on the specific weekday without
            chaging its status on other days. If str_id missing, it will be created
            but set to run only on the specified day.
        """

        try:

            obj = cls.query.filter_by(str_id=str_id).first()
            if obj is None:

                is_repos = str_id.lower().endswith('|empty') or '|empty|' in str_id.lower()

                obj = cls(
                    str_id=str_id,
                    movement_id=cls.create_new_digital_id(locstring=str_id),
                    is_loaded=not is_repos
                )

                LION_SQLALCHEMY_DB.session.add(obj)
                LION_SQLALCHEMY_DB.session.commit()

                obj = cls.query.filter_by(str_id=str_id).first()

            setattr(obj, weekday.lower(), True)
            LION_SQLALCHEMY_DB.session.add(obj)
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            exc_logger.log_exception(popup=True,
                           remarks=f'get_movement_info failed for {str_id}!')

            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def apply_movement_id_mapping(cls, dct_movement_map={}):
        """
        This module will replace local movement movement_id by potentially mapped id once user
        publish schedule. Sinc euser works on a local table, when publishing movements and schedule,
        new movement ids could be created
        """

        if dct_movement_map:

            try:
                for m in dct_movement_map:
                    record = cls.query.filter(cls.movement_id == m).first()
                    if record:
                        record.movement_id = m

                LION_SQLALCHEMY_DB.session.commit()

                return True

            except SQLAlchemyError as err:
                exc_logger.log_exception(popup=True,
                               remarks=f'getting movement_shift_id failed : {str(err)}!')

                LION_SQLALCHEMY_DB.session.rollback()
                return False

            except Exception:
                exc_logger.log_exception(popup=True,
                               remarks=f'getting movement_shift_id failed!')

                LION_SQLALCHEMY_DB.session.rollback()

                return False

        else:
            log_message(f"No mapping movement was required!")
            return True

    @ classmethod
    def create_new_digital_id(cls, locstring=''):

        if locstring.lower().endswith('|empty') or '|empty|' in locstring.lower():
            return cls.create_new_repos_digital_id()

        return cls.create_new_loaded_digital_id()

    @ classmethod
    def create_new_loaded_digital_id(cls):

        try:
            return max([obj.movement_id for obj in cls.query.all()
                        if obj.movement_id < MIN_REPOS_MOVEMENT_ID]) + 1

        except Exception as err:
            if 'max() iterable argument is empty' in str(err).lower():
                pass
            else:
                exc_logger.log_exception(
                    popup=False, remarks=f"Could not get a new digital id!")

        return INIT_LOADED_MOV_ID + 1

    @ classmethod
    def create_new_repos_digital_id(cls):

        try:

            objs = cls.query.filter(
                cls.movement_id >= MIN_REPOS_MOVEMENT_ID).all()

            if objs:
                return max(MIN_REPOS_MOVEMENT_ID,
                           max([obj.movement_id for obj in objs])) + 1

        except SQLAlchemyError as err:
            exc_logger.log_exception(
                popup=False, remarks=f"SQLAlchemyError: Could not get a new repos digital id! {str(err)}")

        except Exception:
            exc_logger.log_exception(
                popup=False, remarks=f"Could not get a new repos digital id!")

        return MIN_REPOS_MOVEMENT_ID + 1

    @ classmethod
    def get_max_movement_ids(cls):
        """
        return max_loaded_id, max_repos_id
        No need to add +1
        """
        # loadm, repos_m = ORM_Global_Movements.get_max_movement_ids()
        # if loadm is None or repos_m is None:
        #     return cls.create_new_loaded_digital_id(), cls.create_new_repos_digital_id()
        # else:
        #   return loadm, repos_m
        
        return cls.create_new_loaded_digital_id(), cls.create_new_repos_digital_id()
        
        

    @ classmethod
    def clear_all(cls):

        try:
            cls.query.delete(synchronize_session=False)
            LION_SQLALCHEMY_DB.session.flush()  # Ensure the delete is executed before commit
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            exc_logger.log_exception(popup=False)

        if not cls.query.all():
            log_message(
                f'The table {cls.__tablename__} has been successfully cleared!')


    @classmethod
    def delete_movements_by_shift_ids(cls, shift_ids=[], logger=exc_logger):
        """
        Deletes movements by their IDs.
        :param movement_ids: List of movement IDs to delete.
        """
        if not shift_ids:
            return

        try:
            cls.query.filter(cls.shift_id.in_(shift_ids)).delete(
                synchronize_session=False)
            
            LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            logger.log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            logger.log_exception(popup=True, remarks=f"Error deleting movements: {err}")
            LION_SQLALCHEMY_DB.session.rollback()
    
    @classmethod
    def delete_unscheduled_movements(cls, logger=exc_logger):
        """
        Deletes all movement records from the database where the `shift_id` is either 0 or None.
        Attempts to commit the deletion to the database. If a SQLAlchemy-related error occurs,
        logs the exception without a popup and rolls back the session. For any other exceptions,
        logs the exception with a popup and also rolls back the session.
        Args:
            logger (Logger, optional): Logger instance used to log exceptions. Defaults to exc_logger.
        """

        try:
            cls.query.filter(cls.shift_id.in_([0, None])).delete(synchronize_session=False)
            LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            logger.log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            logger.log_exception(popup=True, remarks=f"Error deleting movements: {err}")
            LION_SQLALCHEMY_DB.session.rollback()


    @classmethod
    def clean_up_loc_strings(cls, logger=exc_logger):
        """
        This method cleans up the loc_string and tu_dest fields in the ShiftMovementEntry table.
        It ensures that loc_string is only set for changeover movements and updates tu_dest accordingly.
        If loc_string is not a changeover, it clears both loc_string and tu_dest.
        """

        try:
            t0 = datetime.now()
            for record in cls.query.all():
                if len(record.loc_string.split('.')) > 3:
                    record.tu_dest = record.loc_string.split('.')[-2]
                else:
                    record.tu_dest = ''
                    record.loc_string = ''

            LION_SQLALCHEMY_DB.session.commit()
            logging.info(f"Cleaned up loc_strings in {(  datetime.now() - t0).total_seconds():.2f} seconds.")

        except SQLAlchemyError as err:
            logging.error(f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            logging.error(f"Error cleaning up loc_strings: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def __get_datetime(cls, depday, deptime, schedule_day='Mon'):

        try:
            time_obj = datetime.strptime(
                f'0000{deptime}'[-4:], "%H%M").time()
            dep_date_time = datetime.combine(
                LION_DATES[schedule_day], time_obj)

            dep_date_time = dep_date_time + timedelta(days=depday)

            return dep_date_time

        except Exception as e:
            exc_logger.log_exception(f"date time could not be built: {str(e)}")

        return None


    def get_movement_attributes(cls, movement: List | int) -> object:

        base_week_day = 'Mon'
        if isinstance(movement, int):
            movement = [movement]

        all_mov_records = cls.query.filter(cls.movement_id.in_(movement)).all()
        
        class OutputClass:
            def __init__(self):
                pass
        
        dct_output = defaultdict(dict)
        for movObj in all_mov_records:

            try:

                origin, dest, depday, deptime, vehicle, traffic_type = movObj.str_id.split(
                    '|')

                vehicle = int(vehicle)
                depday = int(depday)
                mov_id = movObj.movement_id
                is_repos = traffic_type.lower() == 'empty'
                shift_id = movObj.shift_id

                driving_time, dist = UI_RUNTIMES_MILEAGES.retrieve_travel_time_and_distance(
                    orig=origin, dest=dest, vehicle=vehicle)

                loc_string = movObj.loc_string
                tu_dest = movObj.tu_dest

                locs = []

                if loc_string != '' and tu_dest == '':

                    locs = loc_string.split('.')
                    locs.pop()
                    tu_dest = locs.pop()

                DepDateTime = cls.__get_datetime(
                    depday=depday, deptime=deptime, schedule_day=base_week_day)

                if not DepDateTime:
                    raise ValueError(
                        'Dep date time cannot be None!')

                if driving_time is None:
                    raise ValueError('Driving time was None!')
                
                arrivale_datetime = DepDateTime + timedelta(minutes=driving_time)
                arrday = int('Mon' != arrivale_datetime.strftime("%a"))

                dct_output['deptime'] = deptime
                dct_output['arrival_time'] = int(arrivale_datetime.strftime("%H%M"))
                dct_output['movement_id'] = mov_id
                dct_output['depday'] = depday
                dct_output['arrday'] = arrday
                dct_output['is_repos'] = is_repos
                dct_output['shift_id'] = shift_id
                dct_output['driving_time'] = driving_time
                dct_output['dist'] = dist
                dct_output['loc_string'] = loc_string
                dct_output['tu_dest'] = tu_dest
                dct_output['DepDateTime'] = DepDateTime
                dct_output['ArrDateTime'] = arrivale_datetime
                dct_output['TrafficType'] = traffic_type
                dct_output['VehicleType'] = vehicle

            except Exception:
                error_message = f"{error_message}\nError: {exc_logger.log_exception(
                    popup=False, remarks=f'Error when building {origin}->{dest}->{traffic_type}: {vehicle} movement!')}"

        return dict2class(dct_output)
        
    @classmethod
    def to_dict(cls):

        dict_movements_data = {}
        base_week_day = 'Mon'

        shift_ids = [sid for sid, in cls.query.with_entities(cls.shift_id).filter(cls.shift_id > 0).all()]
        if not shift_ids:
            log_message("No shift records found in the database!")
            return dict_movements_data

        dct_shift_names = DriversInfo.dct_shiftnames(shift_ids=shift_ids)

        dct_shift_names.update({1: MOVEMENT_DUMP_AREA_NAME, 2: RECYCLE_BIN_NAME, 0: 'NotScheduled'})

        all_mov_records = cls.query.all()
        all_mov_records_unplanned = [m for m, in cls.query.with_entities(cls.movement_id).filter(
            and_(cls.is_loaded, cls.shift_id == 0)).all()]

        if not all_mov_records:
            log_message("No movement records found in the database!")
            return dict_movements_data

        error_message = ''

        for movObj in all_mov_records:

            try:

                origin, dest, depday, deptime, vehicle, traffic_type = movObj.str_id.split(
                    '|')

                vehicle = int(vehicle)
                depday = int(depday)
                mov_id = movObj.movement_id
                is_repos = traffic_type.lower() == 'empty'

                if all_mov_records_unplanned and (mov_id in all_mov_records_unplanned):
                    shift_id = 0
                else:
                    shift_id = movObj.shift_id

                if shift_id in [1, 2]:
                    continue

                shiftname = dct_shift_names.get(shift_id, 'UnknownShift')

                driving_time, dist = UI_RUNTIMES_MILEAGES.retrieve_travel_time_and_distance(
                    orig=origin, dest=dest, vehicle=vehicle)

                loc_string = movObj.loc_string
                tu_dest = movObj.tu_dest

                locs = []

                if loc_string != '' and tu_dest == '':

                    locs = loc_string.split('.')
                    locs.pop()
                    tu_dest = locs.pop()

                dct_m = {}

                dct_m['weekday'] = base_week_day
                DepDateTime = cls.__get_datetime(
                    depday=depday, deptime=deptime, schedule_day=base_week_day)

                if not DepDateTime:
                    raise ValueError(
                        'Dep date time cannot be None!')

                if driving_time is None:
                    raise ValueError('Driving time was None!')

                dct_m['DepDateTime'] = DepDateTime
                dct_m['ArrDateTime'] = DepDateTime + timedelta(minutes=driving_time)

                dct_m['MovementID'] = mov_id
                dct_m['From'] = origin
                dct_m['To'] = dest
                dct_m['VehicleType'] = vehicle
                dct_m['TrafficType'] = traffic_type
                dct_m['tu'] = tu_dest
                dct_m['loc_string'] = loc_string

                dct_m['shift'] = shiftname

                dct_m['shift_id'] = shift_id

                dct_m['draggableX'] = False if is_repos else True
                dct_m['draggableY'] = dct_m['draggableX']
                dct_m['is_repos'] = is_repos

                dct_m['DrivingTime'] = driving_time

                dct_m['Utilisation'] = 0.01
                dct_m['PayWeight'] = 0
                dct_m['Pieces'] = 0
                dct_m['Capacity'] = 18000

                dct_m['Dist'] = dist

                dct_m['CountryFrom'] = UI_PARAMS.LION_REGION

                dct_m['last_update'] = datetime.now().strftime('%Y-%m-%d %H%M')

                dct_m = DictMovement(**dct_m)
                dct_m.update_str_id()

            except Exception:
                dct_m = {}
                error_message = f"{error_message}\nError: {exc_logger.log_exception(
                    popup=False, remarks=f'Error when building {origin}->{dest}->{traffic_type}: {vehicle} movement!')}"
                
            if len(dct_m) > 0:
                dict_movements_data[mov_id] = dct_m

        return dict_movements_data
        
