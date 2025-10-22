from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from datetime import datetime


class TimeStamp(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'time_stamp'
    __bind_key__ = 'lion_db'

    setting_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(
        50), nullable=False, primary_key=True)

    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)

    def __init__(self, setting_name, timestamp=datetime.now()):
        self.setting_name = setting_name
        self.timestamp = timestamp

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
