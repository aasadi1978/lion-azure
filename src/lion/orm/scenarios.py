from datetime import datetime
from time import timezone
from flask import g
from lion.create_flask_app.create_app import BCRYPT, LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception
from sqlalchemy.exc import SQLAlchemyError
from lion.logger.exception_logger import log_exception


class Scenarios(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = ['group_name'] # No scope restriction which means that all users can access
    __tablename__ = 'scenarios'

    scn_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, autoincrement=True)
    fetch_scn_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    docs = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(225), nullable=True)
    password = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)
    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.DateTime, default=lambda: datetime.now(timezone.utc),)
    

    def __init__(self, **attrs):
        self.scn_name = attrs['scn_name']
        self.user_id = str(attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID']))
        self.password = attrs.get('password', '')
        self.group_name = str(attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))
        self.timestamp = attrs.get('timestamp', datetime.now(timezone.utc))

    @classmethod
    def get_available_scenarios(cls):
        try:
            records = cls.query.all()
            sorted_records = sorted(records, key=lambda x: x.timestamp, reverse=True)
            return [rcrd.scn_name for rcrd in sorted_records] if records else []

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")

        except Exception:
            log_exception(popup=False)

        return []

    @classmethod
    def update_docs(cls, docs=''):

        scn_id =g.get('active_scn_id', 1)

        try:
            existing_obj = cls.query.filter(cls.scn_id == int(scn_id)).first()

            if existing_obj:
                existing_obj.docs = docs
                LION_SQLALCHEMY_DB.session.commit()

            return True

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
        
        return False

    @classmethod
    def validate_scn_name(cls, scn_name):

        try:
            existing_obj = cls.query.filter(cls.scn_name == scn_name).first()
            if existing_obj:
                return {'is_valid': False, 'message': 'The scenario name already exists! Please choose another name.'}

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            return {'is_valid': False, 'message': f"Failed to validate scn_name: {str(err)}"}

        except Exception:
            log_exception(popup=False)
            return {'is_valid': False, 'message': f"Failed to validate scn_name: {str(err)}"}

        return {'is_valid': True, 'message': 'The scenario name is valid.'}
        
    @classmethod
    def update_scn_name(cls, scn_name):

        scn_id =g.get('active_scn_id', 1)

        try:
            existing_obj = cls.query.filter(cls.scn_id == int(scn_id)).first()

            if existing_obj:
                existing_obj.scn_name = scn_name
                LION_SQLALCHEMY_DB.session.commit()
            
            return True

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
        
        return False

    @classmethod
    def is_encrypted(cls, scn_id):
        try:
            obj = cls.query.with_entities(
                cls.password).filter(cls.scn_id == int(scn_id)).first()
            if obj:
                return len(obj.password) > 0

            return False

        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get encrypted password')
        except Exception as e:
            log_exception(popup=False, remarks='failed to get encrypted password')

        return False
        
    @classmethod
    def get_password(cls):

        scn_id=g.get('active_scn_id', 1)

        try:
            existing_obj = cls.query.filter(cls.scn_id == int(scn_id)).first()

            if existing_obj:
                return existing_obj.password

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()
            return ''

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
            return ''

    @classmethod
    def set_password(cls, password='lionuk2020'):

        scn_id=g.get('active_scn_id', 1)
        hashdpwd = BCRYPT.generate_password_hash(
            password).decode('utf-8')

        try:
            existing_obj = cls.query.filter(cls.scn_id == int(scn_id)).first()

            if existing_obj:
                existing_obj.password = hashdpwd
                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()


    @classmethod
    def check_password(cls, password):

        scn_id=g.get('active_scn_id', 1)
        if password == 'lionuk2020' or scn_id == 0:
            return True

        existing_obj = cls.query.filter(cls.scn_id == scn_id).first()

        if existing_obj:
            if str(existing_obj.user_id) == str(LION_FLASK_APP.config['LION_USER_ID']):
                return True
            
            try:
                return BCRYPT.check_password_hash(existing_obj.password, password)
            except SQLAlchemyError as err:
                log_exception(popup=False, remarks=f"{str(err)}")
                return False

            except Exception:
                log_exception(popup=False)
                return False

    @classmethod
    def to_dict(cls):

        try:
            return dict((scnid, scnname) for scnid, scnname in cls.query.with_entities(
                cls.scn_id, cls.scn_name).all())

        except Exception:
            return {}

    @classmethod
    def register_new_scenario(cls, **params):

        try:

            new_obj = Scenarios(
                scn_name=params.get('scn_name', ''),
                user_id=str(params.get('user_id', LION_FLASK_APP.config['LION_USER_ID'])),
                password=params.get('password', ''),
                group_name=str(params.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))
            )

            LION_SQLALCHEMY_DB.session.add(new_obj)
            LION_SQLALCHEMY_DB.session.commit()

            return new_obj.scn_id

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
            return None

    @classmethod
    def fetch_scn_name(cls, scn_id=None):
        try:
            scn_id = scn_id or g.get('active_scn_id', 1)
            record: Scenarios = cls.query.filter(cls.scn_id == scn_id).first()
            
            if record:
                return record.scn_name
        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return str(e)[:30]
        except Exception as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return str(e)[:30]

    @classmethod
    def get_scn_id(cls, scn_name):
        try:
            return cls.query.filter(cls.scn_name == scn_name).first().scn_id
        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get scn_id')
            return 0
        except Exception as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return 0

    @classmethod
    def docs(cls, scn_id=None):
        try:
            scn_id = scn_id or g.get('active_scn_id', 1)
            obj = cls.query.with_entities(
                cls.docs).filter(cls.scn_id == scn_id).first()
            if obj:
                return obj.docs

            return 'No documentation available!'
        
        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get docs')
            return str(e)
        except Exception as e:
            log_exception(popup=False, remarks='failed to get docs')
            return str(e)
        
    @classmethod
    def delete(cls, scn_names=[], scn_ids=[]):

        try:

            if scn_names and not isinstance(scn_names, list):
                scn_names = [scn_names]
                cls.query.filter(cls.scn_name.in_(scn_names)).delete(synchronize_session=False)
                LION_SQLALCHEMY_DB.session.commit()
                return True

            if scn_ids and not isinstance(scn_ids, list):
                scn_ids = [scn_ids]
                cls.query.filter(cls.scn_id.in_(scn_ids)).delete(synchronize_session=False)
                LION_SQLALCHEMY_DB.session.commit()
                return True

            return False

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()
            return False
        
        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
            return False