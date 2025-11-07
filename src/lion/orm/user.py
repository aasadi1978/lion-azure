from flask import g, has_request_context, session
from sqlalchemy.exc import SQLAlchemyError
from lion.bootstrap.constants import LION_DDEMO_SCN_NAME, LION_DEFAULT_GROUP_NAME
from lion.create_flask_app.create_app import BCRYPT, LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.utils.session_manager import SESSION_MANAGER

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
    current_scn_id= LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False, default=1)

    def __init__(self, **kwargs):

        self.user_id = session.get('lion_current_user_id', None) or g.get('lion_current_user_id', 1)
        self.object_id = str(kwargs.get('object_id', 'guest'))
        self.role = kwargs.get('role', 'Scheduler')
        self.user_name = kwargs.get('user_name', 'Guest')
        self.email = kwargs.get('email', 'guest@host.com')
        self.lang = kwargs.get('lang', 'GB')
        self.password_hash = kwargs.get('password_hash', '')
        self.current_scn_id = SESSION_MANAGER.get('scn_name')

    @classmethod
    def load_user_context(cls, logged_in_as: str = None) -> dict:
        """
        Load and set the user context for the current session.
        This method retrieves the user data from the database, adds group information,
        and sets up the user context with scenario information.
        Returns:
            dict: A dictionary containing user information with the following keys:
                - User model attributes (excluding password_hash)
                - groups: List of user groups
                - lion_current_group: Current active group (defaults to LION_DEFAULT_GROUP_NAME)
                - lion_current_scn_id: Current scenario ID (defaults to 1)
                - lion_current_scn_name: Current scenario name (defaults to LION_DDEMO_SCN_NAME)
        Raises:
            Exception: If user is not found in database (handled internally)
        Note:
            - If no user is found, creates an empty User object
            - Removes password_hash from returned dictionary for security
            - Uses session or g object to get lion_current_group
        """

        lion_current_group = SESSION_MANAGER.get('group_name')
        scn_name = SESSION_MANAGER.get('scn_name')
        
        try:
            
            dct_lion_user: dict = {}
            userobj = cls.query.first() if logged_in_as is None else cls.query.filter(
                cls.user_id == logged_in_as).first()

            if userobj is not None:
                dct_lion_user = userobj.__dict__
            else:
                raise Exception('User not found!')

        except Exception:
            log_exception('user not found!')
            dct_lion_user = User().__dict__

        try:

            dct_lion_user.update({'group_name': lion_current_group or LION_DEFAULT_GROUP_NAME,
                                  'scn_name': scn_name or LION_DDEMO_SCN_NAME})

            dct_lion_user.pop('password_hash', None)
            dct_lion_user.pop('_sa_instance_state', None)

            if has_request_context():
                session['user'] = dct_lion_user

            LION_FLASK_APP.config['LION_USER_ID'] = dct_lion_user['user_id']
            LION_FLASK_APP.config['LION_USER_GROUP_NAME'] = dct_lion_user['group_name']
            LION_FLASK_APP.config['LION_REGION_LANGUAGE'] = dct_lion_user['lang']

        except Exception:
            log_exception('Setting user context failed')
            dct_lion_user = {}

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
        """
        Updates current_scn_idfield to rememebnr user's latest scenario
        """
        try:
            userObj: User = cls.query.first()

            if userObj:
                setattr(userObj, 'current_scn_id', scn_id)
                LION_SQLALCHEMY_DB.session.commit()
            
        except SQLAlchemyError:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception("Failed to set scn_id!")
        except Exception:
            log_exception("Failed to set scn_id!")
    
    @classmethod
    def create_new_user(cls, **kwargs):
        """
        Factory method to create a new User instance.
        Args:
            **kwargs: Keyword arguments corresponding to User attributes.
        Returns:
            User: A new User instance initialized with provided attributes.
        """

        try:
            existing_user = cls.query.filter(cls.user_id == kwargs.get('user_id')).first()
            if existing_user:
                return existing_user
            
            userObj = cls(**kwargs)
            LION_SQLALCHEMY_DB.session.add(userObj)
            LION_SQLALCHEMY_DB.session.commit()
            return userObj if userObj else None
        
        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))
            LION_SQLALCHEMY_DB.session.rollback()
            return None
        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
            return None
