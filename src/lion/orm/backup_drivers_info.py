from collections import defaultdict
from datetime import datetime
from pickle import UnpicklingError
from sqlalchemy import func
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm.operators import Operator
from lion.logger.exception_logger import log_exception
from lion.logger.exception_logger  import log_exception
from lion.logger.status_logger import log_message
from sqlalchemy.exc import SQLAlchemyError
from lion.utils.popup_notifier import show_error
from pickle import dumps as pickle_dumps, loads as pickle_loads
from cachetools import TTLCache

local_dct_drivers_info_cache_backup = TTLCache(maxsize=1000, ttl=3600 * 8)


class BackupDriversInfo(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'lion_db'
    __tablename__ = 'local_drivers_info'

    """
    This table contains detail such as start position, abse location, oeprator name etc
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
    scn_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)

    data = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.LargeBinary, nullable=True, default=None)

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
        self.scn_id = attrs.get('scn_id', None)
        self.del_flag = attrs.get('del_flag', False)
        self.timestamp = attrs.get('timestamp', datetime.now())
        self.data = attrs.get('data', None)

        for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            setattr(self, dy, attrs.get(dy, False))

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

                setattr(record, 'data', pickle_dumps(
                    dct_tours[record.shift_id]))

            LION_SQLALCHEMY_DB.session.commit()
            return True

        except SQLAlchemyError as err:
            log_exception(
                popup=False, remarks=f'save shift data failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

        except UnpicklingError as err:
            log_exception(
                popup=False, remarks=f'save shift data failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as err:
            log_exception(popup=False)
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
    def shift_id_runs_on_weekdays(cls, shift_id=0, weekdays=[]):
        """
        return True or False
        """
        try:
            if shift_id:
                obj = cls.query.filter(cls.shift_id == shift_id).first()
                if obj:
                    status = True
                    for wkday in weekdays:
                        status = status and getattr(obj, wkday.lower(), False)

                    return status

                return False

        except Exception as e:
            log_message(f'shift_id_runs_on_weekdays failed! {e}')
            return False

    @classmethod
    def get_shift_id_running_days(cls, shift_id):
        try:
            return cls.query.filter(cls.shift_id == shift_id).first()

        except Exception as e:
            log_message(f'get_running_days failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return []

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
    def to_sub_dict(cls, shift_ids=[]):

        try:
            dct_drivers_info = local_dct_drivers_info_cache_backup['dct_drivers']
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
            log_exception(popup=False)
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
            log_message(f'get_shift_id_running_days failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
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
        obj = cls.query.filter(cls.shift_id == shift_id).all()

        if obj:
            return obj[0].shiftname

        return 0

    @classmethod
    def dct_shiftnames(cls, shift_ids=[]):

        objs = (cls.query.with_entities(cls.shift_id, cls.shiftname)
                .filter(cls.shift_id.in_(shift_ids))
                .all())

        if objs:
            return dict((sid, sname) for sid, sname in objs)

        return {}

    @ classmethod
    def get_operator(cls, shift_id):

        if shift_id > 2:
            try:
                return local_dct_drivers_info_cache_backup[
                    'dct_drivers'][shift_id]['operator']

            except Exception:

                try:
                    return local_dct_drivers_info_cache_backup.get('dct_drivers', cls.to_dict_all())[
                        shift_id]['operator']

                except Exception:
                    log_exception(popup=False)

            return 'Unknown'

        return ''

    @ classmethod
    def is_doubleman(cls, shift_id):

        if shift_id > 2:
            try:
                return local_dct_drivers_info_cache_backup[
                    'dct_drivers'][shift_id]['double_man']

            except Exception:
                if shift_id in [1, 2]:
                    return False

                try:
                    return local_dct_drivers_info_cache_backup.get('dct_drivers', cls.to_dict_all())[
                        shift_id]['double_man']

                except Exception:
                    log_exception(popup=False)

        return False

    @ classmethod
    def get_vehicle(cls, shift_id):
        try:
            return int(local_dct_drivers_info_cache_backup.get('dct_drivers', cls.to_dict_all())[
                shift_id]['vehicle'])

        except Exception:
            log_exception(popup=True, remarks=f'Vehicle type of {
                           shift_id} could not be determiend!')

        return 0

    @ classmethod
    def get_new_id(cls):

        try:

            next_id = cls.query.with_entities(
                func.max(cls.shift_id)).scalar()

            if not next_id:
                next_id = 1000

        except SQLAlchemyError as err:
            log_message(f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()

        return next_id + 1

    @ classmethod
    def register_new(cls, **kwargs):

        shiftname = kwargs.get('shiftname', kwargs.get(
            'driver_id', kwargs.get('driver id', '')))

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

                driverObj = BackupDriversInfo(**dct_data)
                for dy in running_days:
                    setattr(driverObj, dy.lower(), True)

                LION_SQLALCHEMY_DB.session.add(driverObj)
                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            show_error(f'register_new failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

            return 0

        local_dct_drivers_info_cache_backup['dct_drivers'] = cls.to_dict_all()
        local_dct_drivers_info_cache_backup['dct_operators'] = Operator.to_dict(
        )

        return shift_id

    @ classmethod
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
                driverObj = BackupDriversInfo(**dct_data)

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

        local_dct_drivers_info_cache_backup['dct_drivers'] = cls.to_dict_all()

    @classmethod
    def to_dict(cls, shift_ids=[]):
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

        dct_drivers_info = local_dct_drivers_info_cache_backup.get(
            'dct_drivers', {})
        if not dct_drivers_info:
            dct_drivers_info = cls.to_dict_all()

        try:
            if shift_ids:
                try:
                    return {d: dct_drivers_info[d] for d in shift_ids}
                except Exception:
                    dct_drivers_info = cls.to_dict_all()
                    return {d: dct_drivers_info[d] for d in shift_ids}

            return dct_drivers_info

            # dct_drivers_info = {obj.shift_id: {
            #     'shift_id': obj.shift_id,
            #     'controlled by': obj.ctrl_loc,
            #     'start position': obj.start_loc,
            #     'double_man': obj.double_man,
            #     'vehicle': obj.vehicle,
            #     'driver id': obj.shiftname,
            #     'shiftname': obj.shiftname,
            #     'hbr': obj.home_base,
            #     'home_base': obj.home_base,
            #     'operator': obj.operator,
            #     'loc': obj.loc
            # } for obj in cls.query.filter(cls.shift_id.in_(shift_ids)).all()}

            # if len(dct_drivers_info) == 1:
            #     return dct_drivers_info[shift_ids.pop()]

            # return dct_drivers_info

            # return {obj.shift_id: {
            #         'shift_id': obj.shift_id,
            #         'controlled by': obj.ctrl_loc,
            #         'start position': obj.start_loc,
            #         'double_man': obj.double_man,
            #         'vehicle': obj.vehicle,
            #         'driver id': obj.shiftname,
            #         'shiftname': obj.shiftname,
            #         'hbr': obj.home_base,
            #         'home_base': obj.home_base,
            #         'operator': obj.operator,
            #         'loc': obj.loc
            #         } for obj in cls.query.all()}

        except SQLAlchemyError as err:
            log_message(f'to_dict failed! {str(err)}')

            return {}

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
                'operator': dct_operators.get(obj.operator, 'Unknown opr'),
                'loc': obj.loc
            } for obj in cls.query.all()}

            local_dct_drivers_info_cache_backup['dct_drivers'] = dct_drivers
            local_dct_drivers_info_cache_backup['dct_operators'] = dct_operators

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
            log_exception(
                popup=True, remarks=f"Getting shift names failed: {str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return []

        except ValueError as err:
            log_exception(popup=True, remarks=str(err))
            LION_SQLALCHEMY_DB.session.rollback()
            return []

        except Exception:
            log_exception(popup=True, remarks=f"Getting shift names failed.")
            LION_SQLALCHEMY_DB.session.rollback()

        return []

    @ classmethod
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
            log_exception(popup=True, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

            return False

        except Exception as e:  # It's better to catch a more specific exception if possible
            # Ensure e is converted to string properly
            log_message(f'delete failed! {e}')
            LION_SQLALCHEMY_DB.session.rollback()
            return False  # Returning False on failure for consistency

    @ classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            log_exception('clearing table failed!')

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
            log_exception(popup=False, remarks=str(err))

            return {}

        except UnpicklingError as err:

            log_exception(
                popup=False, remarks="Error unpickling data: {str(err)}")

            return {}

        except Exception:
            log_exception(popup=False)

        return {}

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
            log_exception(popup=False, remarks=str(err))

            return None

        except UnpicklingError as err:

            log_exception(
                popup=False, remarks="Error unpickling data: {str(err)}")

            return None

        except Exception:
            return None
