from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.utils.session_manager import SESSION_MANAGER

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


def retrieve_current_user():
    try:
        if not SESSION_MANAGER.get("user", {}):
            from lion.orm.user import User

            with LION_FLASK_APP.app_context():
                validate_connection()
                user = User.load_user_context()
                if not user:
                    raise Exception('Could not set user context!')
        

        return user['user_id'], user['user_name'], user['group_name']

    except Exception:
        pass
    
    tnow = utcnow().replace(':', '')
    return 1, f'lion-user-{tnow}', f'lion-group-{tnow}'