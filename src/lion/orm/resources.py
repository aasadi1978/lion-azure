import logging
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from sqlalchemy.exc import SQLAlchemyError
from lion.logger.exception_logger import log_exception
from lion.ui.ui_params import UI_PARAMS
from lion.utils.session_manager import SESSION_MANAGER


class Resources(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = ["group_name"]
    __tablename__ = 'resources'

    loc_code = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(50), nullable=False, primary_key=True)

    employed = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)
    subco = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)
    total = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)
    region = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=False)
    user_id = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    group_name = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(150), nullable=True)

    def __init__(self, **attrs):
        self.loc_code = attrs.get('loc_code', '')
        self.employed = attrs.get('employed', 0)
        self.subco = attrs.get('subco', 0)
        self.total = attrs.get('total', 0)
        self.group_name = attrs.get('group_name', SESSION_MANAGER.get('group_name'))
        self.user_id = str(attrs.get('user_id', SESSION_MANAGER.get('user_id')))
        self.scn_id = attrs.get('scn_id', SESSION_MANAGER.get('scn_id'))
        self.region = attrs.get('region', SESSION_MANAGER.get('region', 'GB'))


    @classmethod
    def get_driver_locations(cls):
        try:
            return [loc for loc, in cls.query.with_entities(
                cls.loc_code).filter(cls.total > 0).all()]

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")

        except Exception:
            log_exception(popup=False)

        return []

    @classmethod
    def bulk_import_resources(cls, df_resources=None):

        if df_resources is None or df_resources.empty:
            return False
        
        cls.clear_all()
        list_of_dicts = df_resources.to_dict('records')
        hdrs = df_resources.columns

        if 'loc_code' in hdrs and ('employed' in hdrs or 'subco' in hdrs or 'total' in hdrs):
            try:

                # Precompute total if not present
                for dct in list_of_dicts:

                    dct['employed'] = dct.get('employed', 0)
                    dct['subco'] = dct.get('subco', 0)
                    dct['total'] = dct.get('total', dct['subco'] + dct['employed'])
                    dct['region'] = UI_PARAMS.LION_REGION

                # Perform fast bulk insert
                LION_SQLALCHEMY_DB.session.bulk_insert_mappings(Resources, list_of_dicts)
                LION_SQLALCHEMY_DB.session.commit()

                return True
            
            except SQLAlchemyError as err:
                logging.error(f"Failed to import resources to DB: {str(err)}")
                LION_SQLALCHEMY_DB.session.rollback()
                return False

            except Exception as err:
                logging.error(f"Failed to import resources to DB: {str(err)}")
                LION_SQLALCHEMY_DB.session.rollback()
                return False

        return False

    @classmethod
    def dct_employed_by_user(cls):

        try:
            records = Resources.query.all()
            return {rcrd.loc_code: rcrd.employed for rcrd in records}

        except Exception as err:
            print(str(err))
            LION_SQLALCHEMY_DB.session.rollback()
            return {}

    @classmethod
    def dct_subco_by_user(cls):

        try:
            records = Resources.query.all()
            return {rcrd.loc_code: rcrd.subco for rcrd in records}

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return {}

    @classmethod
    def dct_total_by_user(cls):

        try:
            return dict(cls.query.with_entities(cls.loc_code, cls.total).all())

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return {}

    @classmethod
    def get_loc_employed_drivers(cls, loc_code):

        try:
            records = cls.query.filter(
                cls.loc_code == loc_code).all()
            return records.pop().employed

        except Exception:
            return None

    @classmethod
    def get_loc_subco_drivers(cls, loc_code):

        try:
            records = cls.query.filter(
                cls.loc_code == loc_code).all()
            return records.pop().subco

        except Exception:
            return None
    
    @classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()
            return True
        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(popup=False, remarks='Could not clear resources table!')
            return False

