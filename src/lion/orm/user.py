from os import getlogin
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.create_app import BCRYPT, LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception

class User(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = []
    __tablename__ = 'user'

    user_ladp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True)
    object_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(225), nullable=True)
    user_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(200), nullable=False)
    role = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=False, default='Scheduler')
    password_hash = LION_SQLALCHEMY_DB.Column('password_hash', LION_SQLALCHEMY_DB.String(500), nullable=False, default='')

    def __init__(self, **kwargs):

        self.user_ladp = kwargs['user_ladp']
        self.object_id = kwargs['object_id']
        self.role = kwargs.get('role', 'Scheduler')
        self.password_hash = kwargs['password_hash']
        self.user_name = kwargs['user_name']

    @classmethod
    def set_password(cls, userladp, password):

        try:
            userObj = cls.query.filter(
                cls.user_ladp == userladp).first()

            if userObj:

                userObj.password_hash = BCRYPT.generate_password_hash(
                    password).decode('utf-8')

                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def check_password(cls, userladp, password):

        try:
            password = cls.query.with_entities(cls.password_hash).filter(
                cls.user_ladp == userladp).first()

            paswrd = ''
            if password:
                paswrd = password[0]

            return BCRYPT.check_password_hash(paswrd, password)

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))

        except Exception:
            log_exception(popup=False)

        return BCRYPT.check_password_hash('', password)

    @classmethod
    def change_password(cls, userladp, new_password):

        try:
            usrObj = cls.query.filter(cls.user_ladp == userladp).first()

            if usrObj:

                usrObj.password_hash = BCRYPT.generate_password_hash(
                    new_password).decode('utf-8')
                LION_SQLALCHEMY_DB.session.commit()

                return True

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()

        return False

    @classmethod
    def get_user_name(cls, userladp):
        try:
            userObj = cls.query.filter(
                cls.user_ladp == userladp).first()

            if userObj:
                return userObj.user_name

        except SQLAlchemyError:
            return 'UnknownUser'

        except Exception:
            return 'UnknownUser'

    @classmethod
    def get_purple_id(cls):

        log_id = getlogin()

        try:

            if str(log_id).isnumeric():
                return log_id
            
            userObj = cls.query.filter(
                func.lower(cls.user_ladp) == str(log_id).lower()).first()

            if userObj:
                return userObj.user_ladp

            userObj = cls.query.filter(
                func.lower(cls.orange_id) == str(log_id).lower()).first()

            if userObj:
                return userObj.user_ladp
            
            if log_id=='arasa':

                new_obj = User(
                    user_ladp=1003626416,
                    user_name='Alireza Asadi',
                    orange_id='arasa',
                    proxy='',
                    role='Developer'
                )

                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

                return 1003626416

            raise Exception(f'User not found: {log_id}')

        except SQLAlchemyError:
            log_exception(popup=False, remarks=f'User not found: {log_id}')
            return 0

        except Exception:
            log_exception(popup=False, remarks=f'User not found: {log_id}')
            return 0

    @classmethod
    def user_role(cls):

        try:
            log_id = cls.get_purple_id()

            userObj = cls.query.filter(cls.user_ladp == log_id).first()
            if userObj:
                return userObj.role
            
            raise ValueError(f'User not found: {log_id}')

        except SQLAlchemyError:
            log_exception(popup=False, remarks=f'User not found: {log_id}')
            return 'Unknown'

        except Exception:
            log_exception(popup=False, remarks=f'User not found: {log_id}')
            return 'Unknown'
        

    @classmethod
    def active_user_name(cls):

        try:
            log_id = cls.get_purple_id()

            userObj = cls.query.filter(cls.user_ladp == log_id).first()

            if userObj:
                return userObj.user_name

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))
            return '#ERROR'

        except Exception:
            log_exception(popup=False)
            return '#ERROR'

    @classmethod
    def view_only(cls):

        try:
            log_id = cls.get_purple_id()

            userObj = cls.query.filter(cls.user_ladp == log_id,
                                       cls.role.in_(['Developer', 'Scheduler', 'MasterPlanner'])).first()

            if userObj:
                return False
            
            return str(log_id).lower() not in ['b008ahe', 'l765cwj', 'l875cpq', 'paul binfield', 'mark davis']

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{log_id} is view only: {str(err)}")
            return True

    @classmethod
    def update(cls, **kwargs):

        try:

            userladp = kwargs.get('user_ladp',  '')

            if str(userladp).isnumeric():
                userladp = int(userladp)
            else:
                raise Exception(
                    f'Invalid user id: {userladp}. A numeric user id is required!')

            user_name = kwargs.get('user_name',  '')
            role = kwargs.get('role',  'Scheduler')
            proxy = kwargs.get('proxy',  '')

            existing_obj = cls.query.filter(cls.user_ladp == userladp).first()

            if existing_obj is None:

                new_obj = User(
                    user_ladp=userladp,
                    user_name=user_name,
                    proxy=proxy,
                    role=role
                )
                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

            else:
                existing_obj.user_name = user_name
                existing_obj.role = role
                existing_obj.proxy = proxy
                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(popup=False)
