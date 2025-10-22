from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.orm_azure.scoped_mixins import BASE, GroupScopedBase


class VehicleType(BASE, GroupScopedBase):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'vehicle_type'

    vehicle_code = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False,
                             primary_key=True, autoincrement=True)
    vehicle_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    vehicle_short_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=False)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default='')

    def __init__(self, **attrs):
        self.vehicle_name = attrs.get('vehicle_name', '')
        self.vehicle_short_name = attrs.get('vehicle_short_name', '')
        self.user_id = str(attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID']))
        self.group_name = str(attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))

    @classmethod
    def update(cls, **kwargs):

        try:

            vname = kwargs.get('vehicle_name',  '')
            vsname = kwargs.get('vehicle_short_name',  '')

            existing_obj = VehicleType.query.filter_by(
                vehicle_name=vname
            ).first()

            if existing_obj is None:

                new_obj = VehicleType(
                    vehicle_name=vname,
                    vehicle_short_name=vsname
                )
                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception()

    @classmethod
    def dict_vehicle_name(cls):
        """
        Returns a dict with vehicle code as keys
        """
        try:
            objs = VehicleType.query.all()
            return {obj.vehicle_code: obj.vehicle_name for obj in objs}

        except Exception:
            return {}

    @classmethod
    def dict_vehicle_short_name(cls):
        """
        Returns a dict with vehicle code as keys and shortname in values
        """
        try:
            objs = VehicleType.query.all()
            return {obj.vehicle_code: obj.vehicle_short_name for obj in objs}

        except Exception as err:
            print(str(err))
            return {}

    @classmethod
    def dict_vehicle_code(cls):
        """
        Returns a dict with vehicle names as keys
        """
        try:
            objs = VehicleType.query.all()
            return {obj.vehicle_name: obj.vehicle_code for obj in objs}

        except Exception:
            return {}

    @classmethod
    def get_vehicle_name(cls, vehicle_code):

        try:
            existing_obj = cls.query.filter(
                cls.vehicle_code == vehicle_code
            ).first()

            if existing_obj:
                return existing_obj.vehicle_name
            else:
                return 'Unknown Vehicle'

        except Exception:
            return 'Unknown Vehicle'

    @classmethod
    def get_vehicle_short_name(cls, vehicle_code):

        try:
            existing_obj = VehicleType.query.filter_by(
                vehicle_code=vehicle_code
            ).first()

            if existing_obj is not None:
                return existing_obj.vehicle_short_name
            else:
                return 'Unknown Vehicle'

        except Exception:
            pass
            return 'Unknown Vehicle'

    @classmethod
    def get_vehicle_code(cls, vehicle_name):

        try:
            existing_obj = VehicleType.query.filter_by(
                vehicle_name=vehicle_name
            ).first()

            if existing_obj is not None:
                return existing_obj.vehicle_code
            else:
                existing_obj = VehicleType.query.filter_by(
                    vehicle_name=vehicle_name.lower()
                ).first()

                if existing_obj is not None:
                    return existing_obj.vehicle_code
                else:
                    return None

        except Exception:
            pass

        return None
