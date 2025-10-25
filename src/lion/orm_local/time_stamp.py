from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from datetime import datetime



class TimeStamp(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'local_data_bind'
    

    setting_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(
        50), nullable=False, primary_key=True)

    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default='')

    def __init__(self, **attrs):
        self.setting_name = attrs.get('setting_name', '')
        self.timestamp = attrs.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.user_id = attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID'])
        self.group_name = attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME'])

    @classmethod
    def update(cls, **settings):

        try:
            for setting, set_val in settings.items():

                existing_setting = TimeStamp.query.filter_by(
                    setting_name=setting
                ).first()

                if existing_setting:
                    existing_setting.timestamp = set_val
                else:
                    new_setting = TimeStamp(
                        setting_name=setting,
                        timestamp=set_val
                    )

                    LION_SQLALCHEMY_DB.session.add(new_setting)

            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def to_dict(cls):

        try:
            default_settings = TimeStamp.query.all()

            return {setting.setting_name: setting.timestamp for setting in default_settings}
        except Exception:
            return {}

    @classmethod
    def get_timestamp(cls, setting_name):

        try:
            setting_record = TimeStamp.query.filter_by(
                setting_name=setting_name).first()

            if setting_record:
                return setting_record.timestamp
            else:
                return ''

        except Exception:
            return ''
