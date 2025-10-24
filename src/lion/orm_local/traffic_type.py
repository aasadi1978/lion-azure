from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.orm.scoped_mixins import BASE, GroupScopedBase


class TrafficType(BASE, GroupScopedBase):

    __bind_key__ = 'local_data_bind'
    __tablename__ = 'traffic_type'

    traffic_type = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False,
                             primary_key=True)
    traffic_type_color = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    abbr = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default='')

    def __init__(self, **attrs):
        self.traffic_type = attrs.get('traffic_type', '')
        self.traffic_type_color = attrs.get('traffic_type_color', '')
        self.abbr = attrs.get('abbr', '')
        self.user_id = str(attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID']))
        self.group_name = str(attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))

    @classmethod
    def update(cls, **kwargs):

        try:

            vname = kwargs.get('traffic_type',  '')
            color_code = kwargs.get('traffic_type_color',  '')

            existing_obj = TrafficType.query.filter_by(
                traffic_type=vname
            ).first()

            if existing_obj is None:

                new_obj = TrafficType(
                    traffic_type=vname,
                    traffic_type_color=color_code
                )
                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception()

    @classmethod
    def dct_short_names(cls):

        dct = {}
        try:
            objs = cls.query.all()

            if objs:
                for obj in objs:

                    if obj.abbr:
                        dct[obj.traffic_type] = obj.abbr
                    else:
                        dct[obj.traffic_type] = obj.traffic_type

            return dct

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception()

        return {}

    @classmethod
    def dict_traffic_type(cls):
        """
        Returns a dict with vehicle code as keys and color code in values
        """
        try:
            objs = TrafficType.query.all()
            return {obj.traffic_type: obj.traffic_type_color for obj in objs}

        except Exception:
            return {}

    @classmethod
    def get_traffic_type_color(cls, traffic_type):

        try:
            existing_obj = TrafficType.query.filter_by(
                traffic_type=traffic_type
            ).first()

            if existing_obj is not None:
                return existing_obj.traffic_type_color
            else:
                return '#000000'

        except Exception:
            return '#000000'
