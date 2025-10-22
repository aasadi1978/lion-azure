import logging

from setproctitle import getproctitle
from lion.config import paths
from flask_bootstrap import Bootstrap
from flask import Flask
from flask_bcrypt import Bcrypt
import warnings
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.create_flask_app.config import LION_CONFIG

warnings.filterwarnings("ignore")

class CreateAPP:
    """Singleton class to create and manage the Flask app and Bcrypt instances."""
    _instance = None
    _initialized = False
    _app = None
    _bcrypt = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance._app = None
            cls._instance._bcrypt = None
            cls._instance._initialized = False
                    
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.create()

    def reset_instance(self):
        self._initialized = False
        self._app = None
        self._bcrypt = None

    def lion_flask_app(self):
        if not self._app:
            self.create()
        return self._app

    def bcrypt(self):
        if not self._bcrypt:
            self.create()
        return self._bcrypt

    def get_config(self, config_key: str, default: str | None = None) -> str | None:
        
        if self.is_app_valid():
            self.create()
        
        try:
            conf = self._app.config.get(config_key)
        except Exception as e:
            logging.error(f"Error retrieving config '{config_key}': {e}")
            conf = None

        return conf if conf is not None else default

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_app_valid(self):
        return self._app is not None and self._bcrypt is not None and self._app.config.get('SQLALCHEMY_DATABASE_URI') is not None

    def create(self):

        if self._initialized and self.is_app_valid():
            logging.info(f"Flask app and Bcrypt instances already created for {getproctitle()}")
            return
        
        try:
            lion_app = Flask(__name__,
                        template_folder=paths.LION_TEMPLATES_PATH,
                        static_folder=paths.LION_STATIC_PATH)
            
            Bootstrap(lion_app)
            lion_app.secret_key = 'Lipsol1978'
            # config = configure_lion_app(cold_start=cold_start)

            if not LION_CONFIG:
                logging.critical(f"Failed to configure the Flask app! Exiting the app with code 1 for {getproctitle()}")
                self._app = None
                self._bcrypt = None
                self._initialized = False
                return
            
            lion_app.config.from_mapping(LION_CONFIG)

            LION_SQLALCHEMY_DB.init_app(lion_app)
            bcrypt = Bcrypt(lion_app)

            self._app = lion_app
            self._bcrypt = bcrypt

            self._initialized = True

            if self.is_app_valid():
                logging.info(f"Flask app and Bcrypt instances created successfully for {getproctitle()}")
            else:
                logging.critical(f"Flask app or Bcrypt instance is invalid after creation! Exiting the app with code 1 for {getproctitle()}")
                self._app = None
                self._bcrypt = None
                self._initialized = False

        except Exception as e:
            logging.critical(
                f"Error at flask_app.py. The app could not be initialized! {str(e)} for {getproctitle()}")
            self._app = None
            self._bcrypt = None
            self._initialized = False
        
FLASK_APP_INSTANCE = CreateAPP.get_instance()
LION_FLASK_APP = FLASK_APP_INSTANCE.lion_flask_app()
BCRYPT = FLASK_APP_INSTANCE.bcrypt()
