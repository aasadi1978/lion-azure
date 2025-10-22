from datetime import datetime
from pickle import UnpicklingError
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
import lion.logger.exception_logger as exc_logger
from sqlalchemy.exc import SQLAlchemyError
from pickle import loads as pickle_loads
from cachetools import TTLCache

drivers_info_cache = TTLCache(maxsize=1000, ttl=3600 * 8)


class TempDriversInfo(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'temp_local_schedule_db'
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
        self.del_flag = attrs.get('del_flag', False)
        self.timestamp = attrs.get('timestamp', datetime.now())
        self.data = attrs.get('data', None)

        for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            setattr(self, dy, attrs.get(dy, False))

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

class AzureDriversInfo(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'azure_sql_db'
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

        for dy in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            setattr(self, dy, attrs.get(dy, False))

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
