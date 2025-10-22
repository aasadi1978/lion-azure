from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from cachetools import TTLCache


class TempChangeover(LION_SQLALCHEMY_DB.Model):

    # Temporary changeover data in temp_schedule.db
    __bind_key__ = 'temp_local_schedule_db'
    __tablename__ = 'local_changeovers'

    dct_co_cache = TTLCache(maxsize=100, ttl=900)
    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, primary_key=True, nullable=False)
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(10), nullable=True)
    leg = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)

    def __init__(self, **attrs):

        self.loc_string = attrs.get('loc_string', '')
        # self.idx = attrs.get('idx', 0)
        self.leg = attrs.get('leg', 0)
        self.movement_id = attrs.get('movement_id', 0)
        self.tu_dest = attrs.get('tu_dest', attrs.get(
            'tu', self.loc_string.split('.').pop()))
