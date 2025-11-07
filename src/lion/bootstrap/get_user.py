import logging
from lion.bootstrap.get_user_name import full_name
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.utils.session_manager import SESSION_MANAGER
from os import getenv, getlogin
from lion.utils.on_cloud import ON_CLOUD
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from lion.utils.utcnow import utcnow

def validate_connection():

    connection_failed = False
    from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
    try:
        LION_SQLALCHEMY_DB.session.execute(text("SELECT 1"))
        return
    except SQLAlchemyError:
        connection_failed=True
    except Exception:
        connection_failed=True
    
    if connection_failed:
        from lion.create_flask_app.azure_sql_manager import validate_db_connection
        validate_db_connection(LION_FLASK_APP)

def onboard_user():

    if ON_CLOUD:
        return None

    user_id = str(getlogin())
    from lion.orm.user import User
    with LION_FLASK_APP.app_context():
        if User.create_new_user(
            user_id=user_id,
            user_name=full_name(),
            role='Scheduler',
            group_name=getenv('LION_USER_GROUP_NAME', 'fedex-lion-uk-users'),
            lang=getenv('LION_USER_LANGUAGE_NAME', 'GB'),
        ):
            logging.info(f'User {user_id} has been (already) onboarded!')
            return user_id

        else:
            logging.error(f'User {user_id} could not be onboarded!')
            return None


def retrieve_current_user():
    try:
        logged_in_as = onboard_user()
        if not SESSION_MANAGER.get("user", {}):
            from lion.orm.user import User

            with LION_FLASK_APP.app_context():  
                validate_connection()
                user = User.load_user_context(logged_in_as)
                if not user:
                    raise Exception('Could not set user context!')
        

        return user['user_id'], user['user_name'], user['group_name']

    except Exception:
        pass

    tnow = utcnow(format_str='%Y%m%dT%H%M%S').replace(':', '')
    return 1, f'lion-user-{tnow}', f'lion-group-{tnow}'