from collections import defaultdict
from datetime import datetime
import logging
from pickle import UnpicklingError
from typing import List
from pandas import read_csv
from sqlalchemy import and_, func
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm.operators import Operator
import lion.logger.exception_logger as exc_logger
from lion.logger.status_logger import log_message
from sqlalchemy.exc import SQLAlchemyError
from lion.utils.popup_notifier import show_error
from pickle import dumps as pickle_dumps, loads as pickle_loads
from cachetools import TTLCache
from lion.config.paths import LION_PROJECT_HOME
from lion.ui.ui_params import UI_PARAMS


drivers_info_cache = TTLCache(maxsize=1000, ttl=3600 * 8)


class DriversInfo(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'local_data_bind'
    __tablename__ = 'drivers_info'

    """
    This table contains detail such as start position, absolute location, operator name etc
    per shiftname in the schedule (replaceing dct_drivers)
    """

    shiftname = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    ctrl_loc = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    start_loc = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    operator = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    home_base = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False)
    double_man = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False)
    vehicle = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)
    loc = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    # running_days = db.Column(db.String(25), nullable=False)
    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False, primary_key=True)
    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.DateTime, nullable=False)

    del_flag = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)

    mon = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    tue = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    wed = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    thu = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    fri = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    sat = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    sun = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)

    data = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.LargeBinary, nullable=True, default=None)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default=LION_FLASK_APP.config['LION_USER_GROUP_NAME'])
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default=str(LION_FLASK_APP.config['LION_USER_ID']))

    def __init__(self, **attrs):

        self.shiftname = attrs.get('shiftname', '')
        self.ctrl_loc = attrs.get('ctrl_loc', attrs.get('start_loc', ''))
        self.start_loc = attrs.get('start_loc', attrs.get('ctrl_loc', ''))
        self.operator = attrs.get('operator', 'FedEx Express')
        self.home_base = attrs.get('home_base', attrs.get('hbr', True))
        self.vehicle = attrs.get('vehicle', False)
        self.double_man = attrs.get('double_man', False)
        self.loc = attrs.get('loc', False)
        self.shift_id = attrs.get('shift_id', None)
        self.del_flag = attrs.get('del_flag', False)
        self.timestamp = attrs.get('timestamp', datetime.now())
        self.data = attrs.get('data', None)
        self.group_name = attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME'])
        self.user_id = attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID'])

        for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            setattr(self, dy, attrs.get(dy, False))

    @classmethod
    def clear_cache(cls):

        try:

            drivers_info_cache.pop('dct_drivers', {})
            drivers_info_cache.pop('dct_operators', {})

        except Exception as err:
            exc_logger.log_exception(popup=False)
            log_message(f'save shift data failed! {str(err)}')

        return False

    @classmethod
    def get_all_valid_records(cls):
        try:
            scn_shift_ids_records = cls.query.filter(cls.data.isnot(None)).all()
        except Exception:
            logging.error('get_all_valid_records failed!')
            return []
        return scn_shift_ids_records
    @classmethod
    def shiftname_taken(cls, shift):
        return cls.query.filter(cls.shiftname == shift).first() is None

    @classmethod
    def save_dct_tours(cls,
                       dct_tours={1001: {'driver': 'Alex', 'other_driver_info': {}},
                                  1002: {'driver': 'Mike', 'Mike_driver_info': {}}},
                       timestamp=None):
        """
        This will update base dct_tour in public database.
        The module assumes that the shift to be updated already exist in the
        drivers_info table. So, when creating new shift, it will be saved on both
        drivers_info and lion.shifts (local) tables.
        """

        try:

            shift_ids = list(dct_tours)

            obj_to_modify = cls.query.filter(cls.shift_id.in_(shift_ids)).all()

            if not obj_to_modify:
                return True

            if not timestamp:
                timestamp = datetime.now()

            _user = LION_FLASK_APP.config['LION_USER_ID']

            for record in obj_to_modify:

                record.timestamp = timestamp
                record.user = _user
                record.double_man = record.double_man or dct_tours[record.shift_id].get(
                    'double_man', False)

                setattr(record, 'data', pickle_dumps(
                    dct_tours[record.shift_id]))

            LION_SQLALCHEMY_DB.session.commit()
            return True

        except SQLAlchemyError as err:
            exc_logger.log_exception(
                popup=False, remarks=f'save shift data failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

        except UnpicklingError as err:
            exc_logger.log_exception(
                popup=False, remarks=f'save shift data failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            exc_logger.log_exception(popup=False)
            log_message(f'save shift data failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

        return False

    @classmethod
    def get_weekday_shift_ids(cls, weekday=''):
        """
        return [1001, 1002, ...]
        """
        try:
            objs = [obj for obj in cls.query.all() if getattr(
                obj, weekday.lower(), False)]

            if objs:
                return [obj.shift_id for obj in objs]

        except Exception as e:
            log_message(f'get_weekday_shift_ids failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return []

    @classmethod
    def shift_id_runs_on_weekday(cls, shift_id=0, weekday=''):
        """
        return True or False
        """
        try:
            if shift_id:
                obj = cls.query.filter(cls.shift_id == shift_id).first()
                if obj:
                    return getattr(obj, weekday.lower(), False)

            return False

        except Exception as e:
            log_message(f'shift_id_runs_on_weekday failed! {e}')
            return False

    @classmethod
    def shift_ids_running_on_weekdays(cls, weekdays=[]):
        """
        Returns a list of shift_ids running on all specified weekdays.
        """
        try:

            if weekdays:
                fltr_conditions = [getattr(cls, wkday.lower()) == True for wkday in weekdays]

                return [shift_id for shift_id, in cls.query
                        .with_entities(cls.shift_id)
                        .filter(and_(*fltr_conditions))
                        .all()]
            else:
                return [shift_id for shift_id, in cls.query
                        .with_entities(cls.shift_id)
                        .all()]

        except Exception as e:
            log_message(f'Failed to extract the shift_ids running on {weekdays}: {str(e)}')
            return []

    @classmethod
    def shift_id_runs_on_weekdays_batch(cls, shift_ids=None, weekdays=None):
        """
        Returns a list of shift IDs that are scheduled to run on any of the specified weekdays.
        Args:
            shift_ids (list, optional): List of shift IDs to filter. Defaults to an empty list if not provided.
            weekdays (list, optional): List of weekday names (e.g., ['Monday', 'Tuesday']) to check. Defaults to an empty list if not provided.
        Returns:
            list: List of shift IDs that have at least one of the specified weekdays set to True.
        Notes:
            - Each object is expected to have boolean attributes corresponding to weekday names (e.g., 'monday', 'tuesday', etc.).
            - If an error occurs, logs the error and returns an empty list.
        """

        # Set default values if not provided
        shift_ids = shift_ids or []
        weekdays = weekdays or []

        list_shifts = []

        try:
            # Fetch all objects matching the shift_ids in a single query
            objects = cls.query.filter(cls.shift_id.in_(shift_ids)).all()

            if not objects:
                return []

            # Iterate over each object and check the weekday conditions
            for obj in objects:
                for wkday in weekdays:
                    if getattr(obj, wkday.lower(), False):
                        list_shifts.append(obj.shift_id)
                        break

            return list_shifts

        except Exception as e:
            log_message(
                f'shift_id_runs_on_weekdays_batch failed! Error: {str(e)}')
            return []

    @classmethod
    def shift_id_runs_on_weekdays(cls, shift_id=0, weekdays=[], **kwargs):
        """
        return True or False
        """

        use_or = kwargs.get('use_or', False)
        try:
            if shift_id:
                obj = cls.query.filter(cls.shift_id == shift_id).first()
                if obj:
                    status = not use_or
                    for wkday in weekdays:
                        if use_or:
                            status = status or getattr(
                                obj, wkday.lower(), False)
                        else:
                            status = status and getattr(
                                obj, wkday.lower(), False)

                    return status

                return False

        except Exception as e:
            log_message(f'shift_id_runs_on_weekdays failed! {e}')
            return False

    @classmethod
    def get_running_days(cls, shift_ids=[]):
        """
        return {
            1001: ['Mon', 'Tue', 'Wed', 'Thu'],
            1002: ['Mon', 'Tue', 'Wed', 'Fri']
            }
        """
        try:
            # Fetch only the necessary records where at least one day is True
            if shift_ids:
                objs = cls.query.filter(cls.shift_id.in_(shift_ids)).all()
            else:
                objs = cls.query.all()

            dct_running_days = defaultdict(list)

            for obj in objs:
                for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                    if getattr(obj, dy.lower(), False):
                        dct_running_days[obj.shift_id].append(dy)

            return dct_running_days

        except Exception as e:
            log_message(f'get_running_days failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return {}

    @classmethod
    def get_employed_drivers_per_loc(cls, shift_ids=[]):

        try:
            if not shift_ids:
                return {}

            __dct_employed_driver_locs = defaultdict(set)
            __dct_drivers = cls.to_sub_dict(shift_ids=shift_ids)

            for d in shift_ids:
                if __dct_drivers.get(d, {}).get('operator', '').lower() == 'fedex express':
                    __loc = __dct_drivers.get(d, {}).get('ctrl_loc', None)
                    if __loc:
                        __dct_employed_driver_locs[__loc] = __dct_employed_driver_locs.get(
                            __loc, 0) + 1

            return dict(__dct_employed_driver_locs)

        except Exception:
            exc_logger.log_exception(popup=False)
            return {}

    @classmethod
    def get_dct_shifts_per_weekday(cls):
        try:
            # Fetch only the necessary records where at least one day is True
            objs = cls.query.all()

            dct_data = defaultdict(list)

            for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                dct_data[dy] = [obj.shift_id for obj in objs if getattr(
                    obj, dy.lower(), False)]

            return dct_data

        except Exception as e:
            log_message(f'get_dct_shifts_per_weekday failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return {}

    @classmethod
    def get_shift_id_running_days(cls, shift_id=0):
        """
        return ['Mon', 'Tue', 'Thu']
        """
        try:
            # Fetch only the necessary records where at least one day is True
            obj = cls.query.filter(cls.shift_id == shift_id).first()

            days = []

            if obj:
                for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                    if getattr(obj, dy.lower(), False):
                        days.append(dy)

            return days

        except Exception as e:
            log_message(f'get_shift_id_running_days failed for {shift_id}! {e}')
            return []

    @classmethod
    def get_shift_id(cls, shiftname):
        obj = cls.query.filter(cls.shiftname == shiftname).all()

        if len(obj) > 1:
            show_error(f"We found multiple versions of {
                       shiftname}. Please modify the info through right-click!")

        if obj:
            return obj[0].shift_id

        return 0

    @classmethod
    def get_test_shift_ids(cls):
        return [obj.shift_id for obj in cls.query.all() if '.test.' in obj.shiftname.lower()]

    @classmethod
    def get_shift_name(cls, shift_id):
        try:
            return [shift for shift, in cls.query.with_entities(cls.shiftname).filter(
                cls.shift_id == shift_id).all()].pop() or 'UnknownShift'
        except Exception as e:
            logging.error(f'get_shift_name failed for {shift_id}! {e}')
            return 'UnknownShift'

    @classmethod
    def dct_shiftnames(cls, shift_ids: List = []):

        if shift_ids:
            shift_ids = list(set(shift_ids))

        objs = (cls.query.with_entities(cls.shift_id, cls.shiftname)
                .filter(cls.shift_id.in_(shift_ids))
                .all())

        if objs:
            return dict((sid, sname) for sid, sname in objs)

        return {}

    @classmethod
    def get_operator(cls, shift_id):

        if shift_id > 2:
            try:
                return drivers_info_cache[
                    'dct_drivers'][shift_id]['operator']

            except Exception:

                try:
                    return drivers_info_cache.get('dct_drivers', cls.to_dict_all())[
                        shift_id]['operator']

                except Exception:
                    exc_logger.log_exception(popup=False)

            return 'Unknown'

        return ''

    @classmethod
    def is_doubleman(cls, shift_id):

        if shift_id > 2:
            try:
                return drivers_info_cache[
                    'dct_drivers'][shift_id]['double_man']

            except Exception:
                if shift_id in [1, 2]:
                    return False

                try:
                    return drivers_info_cache.get('dct_drivers', cls.to_dict_all())[
                        shift_id]['double_man']

                except Exception:
                    exc_logger.log_exception(popup=False)

        return False

    @classmethod
    def get_vehicle(cls, shift_id):
        try:
            return int(drivers_info_cache.get('dct_drivers', cls.to_dict_all())[
                shift_id]['vehicle'])

        except Exception:
            exc_logger.log_exception(popup=True, remarks=f'Vehicle type of {
                           shift_id} could not be determiend!')

        return 0

    @classmethod
    def get_new_id(cls):

        if len(cls.query.all()) == 0:
            return 1001

        try:

            next_id = cls.query.with_entities(
                func.max(cls.shift_id)).scalar()

            if not next_id:
                next_id = 1001

        except SQLAlchemyError as err:
            log_message(f"{str(err)}")

        except Exception:
            log_message(f"{exc_logger.log_exception(popup=False)}")

        return next_id + 1

    @classmethod
    def register_new(cls, **kwargs):

        shiftname = kwargs.get('shiftname', kwargs.get(
            'driver_id', kwargs.get('driver id', '')))

        _refresh_cache = kwargs.get('refresh_cache', True)

        if shiftname == '':
            return

        shift_id = kwargs.get('shift_id', 0)
        if not shift_id:
            shift_id = cls.get_new_id()

        shift_id = 1001 if shift_id is None else shift_id

        # dct_data = {
        #     'shift_id': dct_driver['shift_id'],
        #     'ctrl_loc': dct_driver['controlled by'],
        #     'start_loc': dct_driver['start position'],
        #     'double_man': dct_driver.get('double_man', False),
        #     'home_base': dct_driver.get('hbr', True),
        #     'vehicle': dct_driver['vehicle'],
        #     'driver_id': dct_driver.get('driver id', ''),
        #     'loc': dct_driver['loc'],
        #     'operator': dct_driver['operator'],
        #     'shiftname': shiftname if shiftname != '' else dct_driver.get('driver id', '')
        # }

        _vhcle = kwargs.get('vehicle_type', kwargs.get('vehicle', 0))

        dct_data = {
            'shift_id': shift_id,
            'ctrl_loc': kwargs.get('ctrl_loc', kwargs.get('controlled by', shiftname.split('.')[0])),
            'start_loc': kwargs.get('start_loc', kwargs.get('start position', shiftname.split('.')[0])),
            'double_man': kwargs.get('double_man', False),
            'home_base': kwargs.get('home_base', kwargs.get('hbr', True)),
            'vehicle': _vhcle,
            'driver_id': shiftname,
            'loc': kwargs.get('ctrl_loc', kwargs.get('controlled by', shiftname.split('.')[0])),
            'operator': kwargs.get('operator', 'FedEx Express'),
            'shiftname': shiftname
        }

        # if 'operator' not in kwargs.keys():
        #     print('|'.join(list(kwargs.keys())))

        operator_id = Operator.add_operator(operator_name=dct_data['operator'])
        dct_data['operator'] = operator_id

        running_days = kwargs.get('weekdays', [])

        try:
            if not _vhcle:
                raise ValueError("Vehicle type could not be determiend!")

            driverObj = cls.query.filter(
                cls.shift_id == dct_data['shift_id']).first()

            if driverObj:
                log_message(f"{dct_data['shift_id']}|{
                           dct_data['shiftname']} already exists!")

                return driverObj.shift_id
            else:

                driverObj = DriversInfo(**dct_data)
                for dy in running_days:
                    setattr(driverObj, dy.lower(), True)

                LION_SQLALCHEMY_DB.session.add(driverObj)
                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            show_error(f'register_new failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

            return 0

        if _refresh_cache:
            drivers_info_cache['dct_drivers'] = cls.to_dict_all()
            drivers_info_cache['dct_operators'] = Operator.to_dict()

        return shift_id

    @classmethod
    def update_drivers_data(cls, ignore_if_exists=False, **dct_data):

        # if shiftname == '':
        shiftname = dct_data.get(
            'driver id', dct_data.get('shiftname', dct_data.get('driver_id', '')))

        dct_data = {
            'shift_id': dct_data['shift_id'],
            'ctrl_loc': dct_data['controlled by'],
            'start_loc': dct_data.get('start position', dct_data['controlled by']),
            'double_man': dct_data.get('double_man', False),
            'home_base': dct_data.get('hbr', True),
            'vehicle': dct_data['vehicle'],
            'driver_id': dct_data.get('driver id', ''),
            'loc': dct_data['loc'],
            'operator': dct_data['operator'],
            'shiftname': shiftname if shiftname != '' else dct_data.get('driver id', ''),
            'weekdays': dct_data.pop('weekdays', dct_data.pop('running_days', []))
        }

        try:

            if shiftname == '' or 'shift_id' not in dct_data.keys():
                raise KeyError('shift_id and shiftname is required!')

            running_days = [x.lower() for x in dct_data.pop('weekdays', [])]

            driverObj = cls.query.filter(
                cls.shift_id == dct_data['shift_id']).first()

            operator_id = Operator.add_operator(
                operator_name=dct_data['operator'])

            dct_data['operator'] = operator_id

            if driverObj:

                if ignore_if_exists:
                    return

                for k, v in dct_data.items():
                    if k != 'shift_id':
                        setattr(driverObj, k, v)

                if running_days:
                    for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                        if dy in running_days:
                            setattr(driverObj, dy, True)
                        else:
                            setattr(driverObj, dy, False)

                LION_SQLALCHEMY_DB.session.commit()

            else:
                driverObj = DriversInfo(**dct_data)

                if running_days:

                    for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                        if dy in running_days:
                            setattr(driverObj, dy, True)
                        else:
                            setattr(driverObj, dy, False)

                    LION_SQLALCHEMY_DB.session.add(driverObj)
                    LION_SQLALCHEMY_DB.session.commit()

        except Exception as err:
            log_message(f'update_drivers_data failed! {str(err)}')

        drivers_info_cache['dct_drivers'] = cls.to_dict_all()

    @classmethod
    def refresh_cache(cls):
        drivers_info_cache['dct_drivers'] = cls.to_dict_all()
        drivers_info_cache['dct_operators'] = Operator.to_dict()


    @classmethod
    def to_sub_dict(cls, shift_ids=[]):

        try:
            dct_drivers_info = drivers_info_cache['dct_drivers']
        except:
            dct_drivers_info = cls.to_dict_all()

        if 1 in shift_ids:
            shift_ids.remove(1)

        if 2 in shift_ids:
            shift_ids.remove(2)

        try:
            if shift_ids:
                try:
                    return {d: dct_drivers_info[d] for d in shift_ids}
                except Exception:
                    dct_drivers_info = cls.to_dict_all()
                    return {d: dct_drivers_info[d] for d in shift_ids}

            return dct_drivers_info

        except SQLAlchemyError as err:
            log_message(f'to_dict failed! {str(err)}')

            return {}

    @classmethod
    def to_dict(cls):
        """
            return {obj.shift_id: {
                        'shift_id': obj.shift_id,
                        'controlled by': obj.ctrl_loc,
                        'start position': obj.start_loc,
                        'double_man': obj.double_man,
                        'vehicle': obj.vehicle,
                        'driver id': obj.shiftname,
                        'shiftname': obj.shiftname,
                        'hbr': obj.home_base,
                        'operator': obj.operator,
                        'loc': obj.loc
                        } for obj in cls.query.filter(cls.shift_id.in_(shift_ids)).all()}
        """


        try:
            return drivers_info_cache['dct_drivers']
        except:
            cls.to_dict_all()
            return drivers_info_cache['dct_drivers']


    @classmethod
    def to_dict_all(cls):
        """
            return {obj.shift_id: {
                        'shift_id': obj.shift_id,
                        'controlled by': obj.ctrl_loc,
                        'start position': obj.start_loc,
                        'double_man': obj.double_man,
                        'vehicle': obj.vehicle,
                        'driver id': obj.shiftname,
                        'shiftname': obj.shiftname,
                        'hbr': obj.home_base,
                        'operator': obj.operator,
                        'loc': obj.loc
                        } for obj in cls.query.filter(cls.shift_id.in_(shift_ids)).all()}
        """

        try:

            dct_operators = Operator.to_dict()

            dct_drivers = {obj.shift_id: {
                'shift_id': obj.shift_id,
                'controlled by': obj.ctrl_loc,
                'start position': obj.start_loc,
                'double_man': obj.double_man,
                'vehicle': obj.vehicle,
                'driver id': obj.shiftname,
                'shiftname': obj.shiftname,
                'hbr': obj.home_base,
                'home_base': obj.home_base,
                'operator_id': obj.operator,
                'operator': dct_operators.get(obj.operator, 'Unattached'),
                'loc': obj.loc
            } for obj in cls.query.all()}

            drivers_info_cache['dct_drivers'] = dct_drivers
            drivers_info_cache['dct_operators'] = dct_operators

            return dct_drivers

        except SQLAlchemyError as err:
            log_message(f'to_dict failed! {str(err)}')

            return {}

    @classmethod
    def shift_ids_per_weekday(cls, weekdays=[]):
        """
        Note that in the local shifts table, it is allowed to have multiple versions
        of the same shift_id. this module makes sure to get a unique list of those shift_ids
        """

        try:

            latest_records = cls.query.all()

            if weekdays:

                latest_records = [
                    record for record in latest_records
                    if sum(int(getattr(record, wkday.lower(), False)) for wkday in weekdays) == len(weekdays)
                ]

            return [record.shift_id for record in latest_records]

        except SQLAlchemyError as err:
            exc_logger.log_exception(
                popup=True, remarks=f"Getting shift names failed: {str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return []

        except ValueError as err:
            exc_logger.log_exception(popup=True, remarks=str(err))
            LION_SQLALCHEMY_DB.session.rollback()
            return []

        except Exception:
            exc_logger.log_exception(popup=True, remarks=f"Getting shift names failed.")
            LION_SQLALCHEMY_DB.session.rollback()

        return []

    @classmethod
    def remove(cls, shift_ids=[]):
        """
        Deletes shifts by ids provided in the shift_ids list.
        """
        if shift_ids is None:
            shift_ids = []

        try:

            if shift_ids:
                result = cls.query.filter(cls.shift_id.in_(
                    shift_ids)).delete(synchronize_session=False)
            else:
                return False

            LION_SQLALCHEMY_DB.session.commit()
            objs = cls.query.filter(cls.shift_id.in_(shift_ids))
            if not objs:
                log_message(f"{shift_ids[0]} deleted")

            return result

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=True, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return False

        except Exception as e:  # It's better to catch a more specific exception if possible
            # Ensure e is converted to string properly
            log_message(f'delete failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return False  # Returning False on failure for consistency

    @classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            exc_logger.log_exception(f'clearing table failed!')

        if not cls.query.all():
            log_message(
                f'The table {cls.__tablename__} has been successfully cleared!')

    @classmethod
    def load_shifts_data(cls, shiftids=[]):

        try:

            data_content = None
            dct_data = {}

            for shiftid in shiftids:

                contents = (cls.query.with_entities(cls.data)
                            .filter(cls.shift_id == shiftid)
                            .order_by(cls.timestamp.desc())
                            .first())

                if contents:
                    data_content = contents[0]

                if data_content:
                    dct_data[shiftid] = pickle_loads(data_content)

            if dct_data:
                return dct_data

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False, remarks=str(err))

            return {}

        except UnpicklingError as err:

            exc_logger.log_exception(
                popup=False, remarks="Error unpickling data: {str(err)}")

            return {}

        except Exception:
            exc_logger.log_exception(popup=False)

        return {}

    @classmethod
    def clean_up_unused_shifts(cls):
        """
        Deletes all shifts (records) with no running weekday
        """

        try:

            def _has_running_dy(obj):

                try:
                    for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                        if getattr(obj, dy.lower(), False):
                            return True

                except Exception:
                    exc_logger.log_exception(
                        popup=False, remarks=f'Could not determine running day! The record wil not be deleted!')

                    return True

                return False

            all_records = cls.query.all()
            shifts2del = []

            if all_records:

                shifts2del = [
                    rcrd.shift_id for rcrd in all_records if not _has_running_dy(obj=rcrd)]

                if shifts2del:

                    try:
                        cls.query.filter(cls.shift_id.in_(shifts2del)).delete()
                        LION_SQLALCHEMY_DB.session.commit()

                    except SQLAlchemyError as e:
                        log_message(f'clean_up_unused_shifts failed! {e}')
                        LION_SQLALCHEMY_DB.session.rollback()

                    except Exception:
                        LION_SQLALCHEMY_DB.session.rollback()
                        exc_logger.log_exception(
                            popup=False, remarks=f'clean_up_unused_shifts failed!')

        except Exception:
            exc_logger.log_exception(
                popup=False, remarks=f'clean_up_unused_shifts failed!')

            return []

        return shifts2del

    @classmethod
    def load_shift_data(cls, shiftid):
        """
        If no timestamp is given, the latest version of shift data will be loaded
        """

        try:

            data_content = None

            contents = (cls.query.with_entities(cls.data)
                        .filter(cls.shift_id == shiftid)
                        .order_by(cls.timestamp.desc())
                        .first())

            if contents:
                data_content = contents[0]

            if data_content is None:
                return None

            dct_data = pickle_loads(data_content)

            if dct_data:
                return dct_data

        except SQLAlchemyError as err:
            exc_logger.log_exception(popup=False, remarks=str(err))

            return None

        except UnpicklingError as err:

            exc_logger.log_exception(
                popup=False, remarks="Error unpickling data: {str(err)}")

            return None

        except Exception:
            return None

    @classmethod
    def update_suppliers(cls):
        """
        In the case user has a file with a list of shiftnames with asscoicated driver name, then
        this module can update autoamtically if user dumps a csv file called suppliers.csv with two headers [shiftname, supplier], 
        headers must be low case, and place it in LION_PROJECT_HOME director.
        If employed, please use 'FedEx Express'
        """

        if UI_PARAMS.UPDATE_SUPPLIERS:
            UI_PARAMS.UPDATE_SUPPLIERS = False

            try:

                file_path = LION_PROJECT_HOME / 'suppliers.csv'
                if file_path.exists():

                    df_data = read_csv(file_path, sep=',', header=0)
                    df_data.fillna('Unattached')
                    df_data.rename(
                        columns={c: c.lower() for c in df_data.columns.tolist()}, inplace=True)

                    df_data['shiftname'] = df_data.shiftname.apply(
                        lambda x: str(x).strip())

                    df_data['supplier'] = df_data.supplier.apply(
                        lambda x: str(x).strip())

                    df_data['supplier'] = df_data.supplier.apply(
                        lambda x: 'Unattached' if str(x).lower() in [
                            'nan', '', 'unattached', 'null'] else str(x))

                    df_data.set_index('shiftname', inplace=True)
                    dct_data = df_data.supplier.to_dict()

                    shiftnames = set(dct_data.keys())
                    operators = set(dct_data.values())

                    Operator.add_operators(list_of_operators=list(operators))

                    records = cls.query.filter(
                        cls.shiftname.in_(list(shiftnames))).all()

                    if records:

                        for rcrd in records:
                            sname = rcrd.shiftname
                            new_supplier = dct_data[sname]
                            rcrd.operator = 1 if str(new_supplier).lower() in ['employed', 'fedex express'] else (
                                Operator.get_operator_id(new_supplier))

                        LION_SQLALCHEMY_DB.session.commit()

                        Operator.to_dict(clear_cache=True)
                        cls.to_dict_all()

            except SQLAlchemyError as err:
                exc_logger.log_exception(
                    popup=False, remarks=f'update_suppliers failed! {str(err)}')
                LION_SQLALCHEMY_DB.session.rollback()

            except UnpicklingError as err:
                exc_logger.log_exception(
                    popup=False, remarks=f'update_suppliers failed! {str(err)}')
                LION_SQLALCHEMY_DB.session.rollback()

            except Exception as err:

                exc_logger.log_exception(popup=False)
                log_message(f'update_suppliers failed! {str(err)}')
                LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def disable_shiftids_running_days(cls, 
                               shift_ids=[], 
                               weekdays=[],
                               logger=exc_logger):
        """
        Disables the running days for the given shift_ids and weekdays.
        :param shift_ids: List of shift IDs to disable running days for.
        :param weekdays: List of weekdays to disable (e.g., ['Mon', 'Tue', 'Wed']).
        :param logger: Logger instance to log exceptions.
        """
        try:
            all_objs_in_scope = cls.query.filter(
                        cls.shift_id.in_(shift_ids)).all()

            for obj in all_objs_in_scope:
                for dy in weekdays:
                    setattr(obj, dy.lower(), False)

            LION_SQLALCHEMY_DB.session.commit()
            del all_objs_in_scope

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logger.log_exception(popup=False, remarks=f"{str(e)}")

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            logger.log_exception(popup=False)

    @classmethod
    def get_drivers_count_per_loc(cls, logger=exc_logger):
        """
        Returns a dictionary mapping each control location to the count of drivers (shifts) associated with it.
        Queries the database for all unique control locations and counts the number of shift IDs per location.
        Handles SQLAlchemy and generic exceptions by logging them.
        Args:
            logger (Logger, optional): Logger instance for exception logging. Defaults to exc_logger.
        Returns:
            dict: A dictionary where keys are control locations and values are the count of drivers per location.
        """
        try:
            return dict([(loc, cnt) for loc, cnt in cls.query.with_entities(
                cls.ctrl_loc, func.count(cls.shift_id)).group_by(cls.ctrl_loc).all()])
        
        except SQLAlchemyError as e:
            logger.log_exception(popup=False, remarks=f"{str(e)}")

        except Exception:
            logger.log_exception(popup=False)
        
        return {}

    @classmethod
    def get_movement_sequence(cls, logger=exc_logger):

        dct_movement_seq = defaultdict(dict)
        logging.debug('Extracting movement sequence from shifts table ...')

        all_records = cls.query.all()

        if not all_records:
            return {}
        
        for obj in all_records:

            try:
                dct_data = pickle_loads(obj.data)
                if dct_data:
                    movements = dct_data.get('list_movements', [])
                    if movements:
                        dct_movement_seq.update({m: idx + 1 for idx, m in enumerate(movements)})
            except Exception:
                logger.log_exception(popup=False)

        logging.debug(f'Movement sequence has been extracted successfully for {len(dct_movement_seq)} movements.')
        return dct_movement_seq

