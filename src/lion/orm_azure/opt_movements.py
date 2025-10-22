from datetime import datetime
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from sqlalchemy.exc import SQLAlchemyError
from lion.bootstrap.constants import MIN_REPOS_MOVEMENT_ID, INIT_LOADED_MOV_ID
from lion.orm.user_params import UserParams
from lion.logger.exception_logger import log_exception
from lion.logger.status_logger import log_message
from lion.orm_azure.scoped_mixins import BASE, UserScopedBase

# Base = declarative_base()


class OptMovements(BASE, UserScopedBase):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'lion_optimization_db'

    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True, default=0)
    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='reserved')
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')

    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.DateTime, nullable=False)

    mon = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    tue = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    wed = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    thu = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    fri = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    sun = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)

    user_id = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer, nullable=False)

    timestamp = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.DateTime, default=datetime.now())
    
    group_name = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(150), nullable=True)

    # Each Movement can be part of multiple Schedules
    # Note: back_populates should point to 'movement' relation ship created in Schedule class
    # schedules = db.relationship('Schedule', back_populates='movement')

    def __init__(self, **attrs):
        super().__init__(**attrs)

        self.str_id = attrs.get('str_id', '')

        self.movement_id = attrs.get('movement_id', 0)
        self.loc_string = attrs.get('loc_string', '')
        self.tu_dest = attrs.get('tu_dest', '')
        self.shift_id = attrs.get('shift_id', 0)

        self.user_id = str(LION_FLASK_APP.config['LION_USER_ID'])
        self.group_name = str(attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))

        self.timestamp = attrs.get('timestamp', datetime.now())

        for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sun']:
            setattr(self, dy, attrs.get(dy, False))

    @classmethod
    def is_changeover(cls, loc_string):

        try:
            return len(loc_string.split('.')) > 3
        except Exception:
            return False

    @classmethod
    def get_weekday_records(cls, weekday=''):

        try:
            return [obj for obj in cls.query.all()
                    if getattr(obj, weekday.lower(), False)]

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return []

        except Exception:
            log_exception(
                popup=True, remarks='Could not get list of str_ids.')

            LION_SQLALCHEMY_DB.session.rollback()

        return []

    @classmethod
    def get_weekdays_records(cls, weekdays=[]):

        try:

            def __obj_runs_weekdays(obj):

                status = True
                for wkday in weekdays:
                    status = status and getattr(obj, wkday.lower(), False)

                return status

            return [obj for obj in cls.query.all() if __obj_runs_weekdays(obj)]

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            return []

        except Exception:
            log_exception(
                popup=True, remarks='Could not get list of str_ids.')

        return []

    @ classmethod
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
            log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            log_exception(
                popup=True, remarks=f"Error: Could not update shift_ids. {err}")
            LION_SQLALCHEMY_DB.session.rollback()

    @ classmethod
    def get_changeovers_dict(cls):
        """
        returns {'loc_string': [1234, 4567]}
        """

        try:

            all_changeovers = list(set(cls.query.with_entities(
                cls.loc_string).filter(cls.loc_string != '').all()))

            return {rcrd[0]: cls.changeover_shift_ids(rcrd[0])
                    for rcrd in all_changeovers if cls.is_changeover(rcrd[0])}

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"SQLAlchemyError: {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            log_exception(
                popup=True, remarks=f"Error: Could not return list_changeovers. {err}")
            LION_SQLALCHEMY_DB.session.rollback()

        return {}

        # return sorted(list(set(
        #     [f"{obj.loc_string}: {cls.changeover_shifts(obj.loc_string)}" for obj in cls.query.all() if
        #      cls.is_changeover(obj.loc_string)])))

        # return sorted(list(set(
        #     [f"{obj.loc_string}: {cls.changeover_shifts(obj.loc_string)}" for obj in cls.query.all() if
        #      cls.is_changeover(obj.loc_string)])))

    @ classmethod
    def changeover_shift_ids(cls, loc_string=''):
        """
        return list like [1234, 3456]
        """

        try:

            return [obj[0] for obj in
                    cls.query.with_entities(cls.shift_id).filter(cls.loc_string == loc_string)]

        except SQLAlchemyError as e:
            log_exception(
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
            log_exception(
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
            log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return {}

    @ classmethod
    def changeover_movements(cls, loc_string=''):

        try:
            return [obj.movement_id for obj in cls.query.all(
            ) if obj.loc_string == loc_string]

        except Exception:
            log_exception(
                popup=True, remarks=f'Could not get list of str_ids due to a database error.')

        return []

    @ classmethod
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
            log_exception(popup=True,
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

            new_obj = OptMovements(
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
            log_exception(popup=True,
                           remarks=f'get_movement_info failed for {str_id}!')

            LION_SQLALCHEMY_DB.session.rollback()

        return None

    @ classmethod
    def add_dct_m(cls, dct_m={}):
        """

        Note: dct_m must be DictMovement type
        creates a new records if missing. Specify running days, otherwise, default
        setting will be used, i.e., mon-fri; If record exists, it updates data accordingly
        """

        try:

            record = cls.query.filter_by(
                str_id=dct_m['str_id']).first()

            if record is not None:

                if dct_m.get('tu', '') == '':

                    tu_dest = dct_m['loc_string'].split('.')[:-1].pop()
                    dct_m['tu'] = tu_dest

                record.movement_id = dct_m['MovementID']
                record.extended_str_id = dct_m.extended_str_id
                record.str_id = dct_m['str_id']
                record.loc_string = dct_m['loc_string']
                record.tu_dest = dct_m['tu']
                record.shift_id = dct_m['shift_id']

                LION_SQLALCHEMY_DB.session.commit()

            else:

                if dct_m.get('tu', '') == '':

                    tu_dest = dct_m['loc_string'].split('.')[:-1].pop()
                    dct_m['tu'] = tu_dest

                is_repos = dct_m['str_id'].lower().endswith(
                    '|empty') or '|empty|' in dct_m['str_id'].lower()

                record = OptMovements(str_id=dct_m['str_id'],
                                      movement_id=dct_m['MovementID'],
                                      is_loaded=not is_repos,
                                      loc_string=dct_m['loc_string'],
                                      tu_dest=dct_m['tu'],
                                      shift_id=dct_m['shift_id'])

                LION_SQLALCHEMY_DB.session.add(record)

            LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_exception(popup=True,
                           remarks=f"databse error: get_movement_info {dct_m['str_id']}!: {str(err)}")

            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=True,
                           remarks=f"get_movement_info failed for {dct_m['str_id']}!")

            LION_SQLALCHEMY_DB.session.rollback()

        return None

    @ classmethod
    def update_movement_info(cls, dct_m):
        """
        Note: dct_m must be DictMovement type
        Updates information of an existing movement using digital movement id.
        Running days will not be changed
        """

        try:

            record = cls.query.filter(
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
            log_exception(popup=True,
                           remarks=f"updating movement info was not successfull. db error: {str(err)}")

            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=True,
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

                obj = OptMovements(
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
            log_exception(popup=True,
                           remarks=f'get_movement_info failed for {str_id}!')

            LION_SQLALCHEMY_DB.session.rollback()

    @ classmethod
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

            except SQLAlchemyError as err:
                log_exception(popup=True,
                               remarks=f'getting movement_shift_id failed : {str(err)}!')

                LION_SQLALCHEMY_DB.session.rollback()

            except Exception:
                log_exception(popup=True,
                               remarks=f'getting movement_shift_id failed!')

                LION_SQLALCHEMY_DB.session.rollback()

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
                log_exception(
                    popup=False, remarks=f"Could not get a new digital id!")

        return INIT_LOADED_MOV_ID + 1

    @ classmethod
    def create_new_repos_digital_id(cls):

        try:

            return max(MIN_REPOS_MOVEMENT_ID,
                       max([obj.movement_id for obj in cls.query.all()])) + 1

        except Exception:
            log_exception(
                popup=False, remarks=f"Could not get a new repos digital id!")

        return MIN_REPOS_MOVEMENT_ID + 1

    @ classmethod
    def get_max_movement_ids(cls):
        """
        return max_loaded_id, max_repos_id
        No need to add +1
        """
        return cls.create_new_loaded_digital_id(), cls.create_new_repos_digital_id()

    @ classmethod
    def clear_all(cls):

        try:
            LION_SQLALCHEMY_DB.session.query(cls).delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(popup=False)

        if not cls.query.all():
            log_message(
                f'The table {cls.__tablename__} has been successfully cleared!')

