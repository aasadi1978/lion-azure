from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception


class TempScnInfo(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'temp_local_schedule_db'
    __tablename__ = 'scn_info'

    param = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False, primary_key=True)
    val = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False)

    def __init__(self, param, val):
        self.param = param
        self.val = val

    @classmethod
    def scn_name(cls):
        try:
            return cls.query.filter(cls.param == 'scn_name').first().val
        except Exception as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return str(e)[:30]
