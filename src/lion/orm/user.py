from flask import g, session
from sqlalchemy.exc import SQLAlchemyError
from lion.bootstrap.constants import LION_DEFAULT_GROUP_NAME
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
    last_picked_scn_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer)

    def __init__(self, **kwargs):

        self.user_id = str(kwargs.get('user_id', 'guest'))
        self.object_id = str(kwargs.get('object_id', 'guest'))
        self.role = kwargs.get('role', 'Scheduler')
        self.user_name = kwargs.get('user_name', 'Guest')
        self.email = kwargs.get('email', 'guest@host.com')
        self.lang = kwargs.get('lang', 'GB')
        self.password_hash = kwargs.get('password_hash', '')
        self.last_picked_scn_id = kwargs.get('last_picked_scn_id', session.get('current_scn_id', None) or g.get('current_scn_id', 1))

    @classmethod
    def load_user(cls):

        current_group = session.get('current_group', None) or g.get('current_group', None)
        
        try:
            
            dct_lion_user: dict = {}
            userobj = cls.query.first()

            if userobj is not None:
                dct_lion_user = userobj.__dict__
            else:
                guest = User()
                dct_lion_user = guest.__dict__

            dct_lion_user.setdefault('groups', GroupName.get_user_groups())
            del dct_lion_user['password_hash']
            
        except Exception:
            log_exception('user not found!')
            dct_lion_user = {'user_id': 'guest',
                             'group_name': LION_DEFAULT_GROUP_NAME,
                             'user_name': 'Guest'
                             }

        session['current_user'] = dct_lion_user
        session['current_group'] = current_group or LION_DEFAULT_GROUP_NAME
        g.current_user = dct_lion_user
        g.current_group = current_group or LION_DEFAULT_GROUP_NAME

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
    def set_scn_id(cls, scn_id):
        try:
            userObj: User = cls.query.first()

            if userObj:
                userObj.last_picked_scn_id = scn_id
                LION_SQLALCHEMY_DB.session.commit()
            
        except SQLAlchemyError:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception("Failed to set scn_id!")
            return True
