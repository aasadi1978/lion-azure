from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception


class DriverReport(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'driver_report'

    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False, primary_key=True)
    driver = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=True)
    start_point = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, primary_key=True)
    end_point = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    start_time = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, primary_key=True)
    end_time = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    driving_time = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)
    dist_miles = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)
    traffic_type = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    break_info = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    driver_loc = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    lat = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Double, nullable=True)
    lon = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Double, nullable=True)
    driver_loc_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    remarks = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    notes = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    nshifts = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)
    vehicle = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    operator = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    weekday = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    dep_day = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    last_update = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    title = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)

    def __init__(self, **attrs):
        for attr in attrs:
            setattr(self, attr, attrs[attr])

    @classmethod
    def delete_shift_id(cls, shift_id):
        try:
            cls.query.filter(cls.shift_id == shift_id).all().delete()
            LION_SQLALCHEMY_DB.session.commit()
        except Exception:
            log_exception(popup=False)
