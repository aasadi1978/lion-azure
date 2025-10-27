from flask import g, session
from sqlalchemy.exc import SQLAlchemyError
from lion.create_flask_app.create_app import BCRYPT
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.orm.groups import GroupName

class User(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = ['user_id']
    __tablename__ = 'user'

    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), primary_key=True)
    object_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(225), nullable=True)
    user_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(200), nullable=False)
    email = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(200), nullable=False)
    role = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=False, default='Scheduler')
    password_hash = LION_SQLALCHEMY_DB.Column('password_hash', LION_SQLALCHEMY_DB.String(500), nullable=False, default='')
    lang = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=False, default='GB') 

    def __init__(self, **kwargs):

        self.user_id = str(kwargs.get('user_id', self.user_id))
        self.object_id = kwargs['object_id']
        self.role = kwargs.get('role', 'Scheduler')
        self.user_name = kwargs['user_name']
        self.email = kwargs['email']
        self.lang = kwargs.get('lang', 'GB')
        self.password_hash = kwargs.get('password_hash', '')

    @classmethod
    def load_user(cls):

        dct_lion_user: dict = {}
        try:
            userobj = cls.query.first()
            dct_lion_user = userobj.__dict__
            dct_lion_user.setdefault('groups', GroupName.get_user_groups())

            del dct_lion_user['password_hash']
            
        except Exception:
            log_exception('user not found!')
            dct_lion_user = {}


        session['current_user'] = dct_lion_user
        g.current_user = dct_lion_user

        return dct_lion_user

    @classmethod
    def set_password(cls, userid, password):

        try:
            userObj = cls.query.filter(
                cls.user_id == userid).first()

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
    def check_password(cls, userid, password):

        try:
            password = cls.query.with_entities(cls.password_hash).filter(
                cls.user_id == userid).first()

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
    def change_password(cls, userid, new_password):

        try:
            usrObj = cls.query.filter(cls.user_id == userid).first()

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
    def get_user_name(cls, userid):
        try:
            userObj = cls.query.filter(
                cls.user_id == userid).first()

            if userObj:
                return userObj.user_name

        except SQLAlchemyError:
            return 'UnknownUser'

        except Exception:
            return 'UnknownUser'

    @classmethod
    def get_active_user_id(cls):

        try:

            userobj = [id for id, in cls.query.with_entities(cls.user_id).all()]
            if userobj:
                return userobj[0]

        except SQLAlchemyError:
            log_exception(popup=False, remarks=f'User not found')

        except Exception:
            log_exception(popup=False, remarks=f'User not found')

        return 0

    @classmethod
    def user_role(cls):

        try:
            log_id = cls.get_active_user_id()

            userObj = cls.query.filter(cls.user_id == log_id).first()
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
            log_id = cls.get_active_user_id()

            userObj = cls.query.filter(cls.user_id == log_id).first()

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
            log_id = cls.get_active_user_id()

            userObj = cls.query.filter(cls.user_id == log_id,
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

            userid = str(kwargs.get('user_id',  ''))

            user_name = kwargs.get('user_name',  '')
            role = kwargs.get('role',  'Scheduler')
            proxy = kwargs.get('proxy',  '')

            existing_obj = cls.query.filter(cls.user_id == userid).first()

            if existing_obj is None:

                new_obj = User(
                    user_id=userid,
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
