from datetime import datetime
from os import getenv
from lion.config.paths import LION_LOG_FILE_PATH
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from sqlalchemy.exc import SQLAlchemyError
import logging



class LogEntry(LION_SQLALCHEMY_DB.Model):
    """
    Logs application events to the database. Each log entry includes a timestamp, log level, message, and user ID.
    Status.log info.
    """

    __bind_key__ = 'lion_db'
    __tablename__ = 'logger'

    timestamp = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.DateTime, nullable=True, default=datetime.now(), primary_key=True)
    level = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(50), nullable=True, default='INFO')
    message = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=True)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True, default=LION_FLASK_APP.config.get('LION_USER_ID'))

    def __init__(self, **attrs):
        self.level = attrs.get('level', 'INFO')
        self.message = attrs.get('message', '')
        self.timestamp = attrs.get('timestamp', datetime.now())
        self.user_id = attrs.get('user_id', LION_FLASK_APP.config.get('LION_USER_ID'))

    @classmethod
    def clear_log(cls):
        """
        Clears all log entries from the database.
        """
        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

            with open(LION_LOG_FILE_PATH, 'w'):
                pass

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.critical(f"Clearing log failed. {str(e)}")
            return

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.critical(f"Clearing log failed. {str(e)}")
            return

        if getenv('LION_ENV', 'local').upper() == 'LOCAL':
            logging.info("Log cleared.")

    @classmethod
    def export_log(cls, log_id=None, max_entries=None) -> list[str]:
        """
        Exports top `max_entries` log entries from the database.
        """

        try:

            if log_id:

                log_entry = cls.query.filter_by(cls.id == log_id).first()

                if log_entry is not None:
                    return log_entry
            else:
                if max_entries:
                    entries = cls.query.order_by(cls.timestamp.desc()).limit(max_entries) or []
                else:
                    entries = cls.query.order_by(cls.timestamp.desc()).all() or []

                if entries:
                    return [f"{entry.level}|{entry.timestamp}: {entry.message}" for entry in entries]

            return []

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            return [logging.critical(f"Reading log entry failed. {str(e)}")]
        
        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return [logging.critical(f"Reading log entry failed.")]
        
    @classmethod
    def logging_message(cls, message: str, level: str = 'INFO'):

        try:
            log_levels = {
                'DEBUG': logging.debug,
                'INFO': logging.info,
                'WARNING': logging.warning,
                'ERROR': logging.error,
                'CRITICAL': logging.critical
            }

            log_func = log_levels.get(str(level).upper(), logging.info)
            log_func(message)

        except Exception as e:
            logging.error(f"Logging message failed. {str(e)}")

    @classmethod
    def log_entry(cls, **kwargs):

        try:
            message = kwargs.get('message', '')
            level = kwargs.get('level', 'INFO')

            if message:

                log_entry = cls(
                    message=message,
                    level=level
                )

                LION_SQLALCHEMY_DB.session.add(log_entry)
                LION_SQLALCHEMY_DB.session.commit()

                cls.logging_message(message=message, level=level)

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.critical(f"log_entry failed. {str(e)}")

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.critical(f"log_entry failed.")
