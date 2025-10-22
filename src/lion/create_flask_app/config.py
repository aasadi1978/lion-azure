import logging
from os import getenv
from lion.bootstrap import LION_BOOTSTRAP_CONFIG as lion_config # Loaded first to setup env variables and logging in bootstrap\__init__.py
from lion.config import paths
from lion.bootstrap.user_region_and_language import get_lang, get_rgn
from lion.bootstrap.constants import (LION_MASTER_DATABASE_NAME, LION_OPTIMIZATION_DATABASE_NAME, LION_SCHEDULE_DATABASE_NAME, 
                                      LION_TEMP_SCENARIO_DATABASE_NAME, LION_USER_DATABASE_NAME)
from lion.create_flask_app.azure import azure_connection


def configure_lion_app() -> dict:
    """
    Setup the application configuration.
    """

    try:
        db_files = {
            'lion_db': LION_USER_DATABASE_NAME, # For local user configuration
            'local_schedule_db': LION_SCHEDULE_DATABASE_NAME, # For output schedule incl corresponsing movements and schedule
            'temp_local_schedule_db': LION_TEMP_SCENARIO_DATABASE_NAME, # Temporary local schedule
            'lion_master_data_db': LION_MASTER_DATABASE_NAME, # Master data such as runtimes, locations, etc.
            'lion_optimization_db': LION_OPTIMIZATION_DATABASE_NAME # Optimization data
        }

        db_paths = {key: paths.LION_SQLDB_PATH / filename for key, filename in db_files.items()}

        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_paths.pop('lion_master_data_db')}"

        lion_config.update({
            'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'LION_USER_ID': int(lion_config.get('LION_USER_ID', 0)),
            'SQLALCHEMY_BINDS': {key: f"sqlite:///{path}" for key, path in db_paths.items()}
            })

        lion_config['SQLALCHEMY_BINDS']['azure_sql_db'] = azure_connection()
        user_group = getenv('LION_USER_GROUP_NAME', "")
        lion_config.update({'LION_USER_GROUP_NAME': user_group})
        lion_config.update({'LION_USER_REGION_NAME': lion_config.get("LION_USER_REGION_NAME", "") if len(lion_config.get("LION_USER_REGION_NAME", "")) >= 2 else get_rgn(user_group)})
        lion_config.update({'LION_USER_LANGUAGE_NAME': lion_config.get("LION_USER_LANGUAGE_NAME", "") if len(lion_config.get("LION_USER_LANGUAGE_NAME", "")) >= 2 else get_lang(user_group)})

    except Exception as e:
        logging.error(f"[FATAL] Failed to load or parse flask config: {e}")
        return {}
    
    return lion_config

LION_CONFIG = configure_lion_app()

# def configure_lion_app(cold_start: bool = False) -> dict:
#     """
#     Setup the application configuration.
#     """
#     lion_config: dict = {}

#     if cold_start and Path('config.json').exists():
#         lion_config = lion_config_cold_reload()

#         if lion_config:
#             return lion_config
#         else:
#             logging.warning("config.json is empty or not found. Reloading default configuration ...")
    
#     if Path('config.json').exists():
#         with open('config.json') as config_file:
#             lion_config = json.load(config_file)

#     try:
#         db_files = {
#             'lion_db': LION_USER_DATABASE_NAME, # For local user configuration
#             'local_schedule_db': LION_SCHEDULE_DATABASE_NAME, # For output schedule incl corresponsing movements and schedule
#             'temp_local_schedule_db': LION_TEMP_SCENARIO_DATABASE_NAME, # Temporary local schedule
#             'lion_master_data_db': LION_MASTER_DATABASE_NAME, # Master data such as runtimes, locations, etc.
#             'lion_optimization_db': LION_OPTIMIZATION_DATABASE_NAME, # Optimization data
#         }

#         db_paths = {key: paths.LION_SQLDB_PATH / filename for key, filename in db_files.items()}

#         SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_paths.pop('lion_master_data_db')}"

#         lion_config.update({
#             'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
#             'SQLALCHEMY_TRACK_MODIFICATIONS': False,
#             'LION_USER_ID': int(lion_config.get('LION_USER_ID', 0)),
#             'SQLALCHEMY_BINDS': {key: f"sqlite:///{path}" for key, path in db_paths.items()}
#             })

#         user_group = getenv('LION_USER_GROUP_NAME', "")
#         lion_config.update({'LION_USER_GROUP_NAME': user_group})
#         lion_config.update({'LION_USER_REGION_NAME': lion_config.get("LION_USER_REGION_NAME", "") if len(lion_config.get("LION_USER_REGION_NAME", "")) >= 2 else get_rgn(user_group)})
#         lion_config.update({'LION_USER_LANGUAGE_NAME': lion_config.get("LION_USER_LANGUAGE_NAME", "") if len(lion_config.get("LION_USER_LANGUAGE_NAME", "")) >= 2 else get_lang(user_group)})

#         with open('config.json', 'w') as config_file:
#             json.dump(lion_config, config_file, indent=4)

#     except Exception as e:
#         logging.error(f"[FATAL] Failed to load or parse flask config: {e}")
#         return {}
    
#     return lion_config