import logging
from typing import List, Set
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.status_logger import log_message
from lion.utils.popup_notifier import show_error
from sqlalchemy.exc import SQLAlchemyError
from cachetools import TTLCache
from lion.orm.shift_movement_entry import ShiftMovementEntry


class Changeover(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = LION_FLASK_APP.config.get(
        'LION_USER_SPECIFIED_BIND', 'local_schedule_db')
    __tablename__ = 'local_changeovers'

    dct_co_cache = TTLCache(maxsize=100, ttl=900)
    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, primary_key=True, nullable=False)
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(10), nullable=True)
    leg = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True, default=LION_FLASK_APP.config['LION_USER_GROUP_NAME'])
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True, default=LION_FLASK_APP.config['LION_USER_ID'])

    def __init__(self, **attrs):

        self.loc_string = attrs.get('loc_string', '')
        # self.idx = attrs.get('idx', 0)
        self.leg = attrs.get('leg', 0)
        self.movement_id = attrs.get('movement_id', 0)
        self.tu_dest = attrs.get('tu_dest', attrs.get(
            'tu', self.loc_string.split('.').pop()))

        self.group_name = attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME'])
        self.user_id = attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID'])

    @classmethod
    def list_changeovers(cls, clear=False):

        lst = []
        if not clear:
            try:
                return cls.dct_co_cache['list_changeovers']
            except Exception:
                lst = []
                clear = True

        if not lst or clear:

            try:
                loc_strings = [x for x, in cls.query.with_entities(cls.loc_string).all()]
                loc_strings = [x for x in loc_strings if x in ShiftMovementEntry.loc_strings()]

                list_changeovers = []
                for locstr in set(loc_strings):
                    list_changeovers.append(
                        f"{locstr} ({loc_strings.count(locstr)})")

                cls.dct_co_cache['list_changeovers'] = list_changeovers

            except Exception as err:
                log_message(f'list_changeovers creation failed! {str(err)}')

            return list_changeovers

    @classmethod
    def clear_cache(cls):

        try:
            cls.dct_co_cache.clear()
            cls.dct_co_cache = TTLCache(maxsize=100, ttl=900)
        except Exception as err:
            log_message(f'clear_cache failed! {str(err)}')

    @classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception as err:
            log_message(f'clearing table failed! {str(err)}')

    @classmethod
    def get_legs(cls, loc_string=''):

        try:
            objs = cls.query.filter(cls.loc_string == loc_string).all()

            if objs:
                sorted_objs = sorted(objs, key=lambda x: x.leg)
                return [obj.movement_id for obj in sorted_objs]

            return []

        except SQLAlchemyError as e:
            show_error(f"Could not get movs for {
                       loc_string}: {str(e)}")

        except Exception as e:
            show_error(f"Could not movs for {
                       loc_string}: {str(e)}")

        return []

    @classmethod
    def get_movement_loc_string(cls, movment_id=0):

        try:
            obj = cls.query.filter(cls.movement_id == movment_id).first()

            if obj:
                loc_string = obj.loc_string
                legs = len(cls.query.filter(
                    cls.loc_string == loc_string).all())

                return loc_string, f"{obj.leg}/{legs}"

            return '', '1/1'

        except SQLAlchemyError as e:
            show_error(f"Could not get changeove string for {
                       movment_id}: {str(e)}")

        except Exception as e:
            show_error(f"Could not get changeove string for {
                       movment_id}: {str(e)}")

        return '', '1/1'

    @classmethod
    def delete_changeovers(cls, loc_string: List | Set | str) -> bool:

        try:

            if isinstance(loc_string, str):
                loc_string = [loc_string]
            
            loc_strings_to_del = set(loc_string)

            changeover_records = set([locstr for locstr, in cls.query.with_entities(
                cls.loc_string).filter(cls.loc_string.in_(loc_strings_to_del)).all()])
            if not changeover_records:
                return True

            logging.info(f"Identfied {len(changeover_records)} changeover(s) to delete for loc_string(s): {', '.join(changeover_records)}")

            deleted_count = cls.query.filter(
                cls.loc_string.in_(loc_strings_to_del)).delete(synchronize_session=False)

            LION_SQLALCHEMY_DB.session.commit()

            cls.list_changeovers(clear=True)

            if deleted_count:
                logging.info(f"{len(changeover_records)} Changeover(s) have been deleted successfully.")

            return deleted_count > 0

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            show_error(f"SQLAlchemyError: Could not delete changeover with loc_string '{loc_string}': {str(e)}")
            return False

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            show_error(f"General Exception: Could not delete changeover with loc_string '{loc_string}': {str(e)}")
            return False

    @classmethod
    def register_new(cls, loc_string, tu_dest='',
                     dct_movements={1: 1000001, 2: 1000002}):

        try:
            if loc_string == '' or not dct_movements:
                return

            obj = cls.query.filter(cls.loc_string == loc_string).first()
            if obj:

                cls.query.filter(cls.loc_string == loc_string).delete()
                LION_SQLALCHEMY_DB.session.commit()

            if tu_dest == '':
                locs = loc_string.split('.')[:-1]
                tu_dest = locs.pop()

            for lg in dct_movements:

                new_record_leg = Changeover(
                    loc_string=loc_string, tu_dest=tu_dest,
                    movement_id=dct_movements[lg],
                    leg=lg)

                LION_SQLALCHEMY_DB.session.add(new_record_leg)

            LION_SQLALCHEMY_DB.session.commit()
            cls.list_changeovers(clear=True)

        except SQLAlchemyError as e:
            show_error(f"Failed to register new changeover for {
                       loc_string}: {str(e)}")

            LION_SQLALCHEMY_DB.session.rollback()

        except Exception as e:
            show_error(f"Failed to register new changeover for {
                       loc_string}: {str(e)}")

            LION_SQLALCHEMY_DB.session.rollback()


if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        LION_SQLALCHEMY_DB.create_all()
