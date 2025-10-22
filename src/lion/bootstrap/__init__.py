import logging
from lion.bootstrap.load_bootstrap import LION_ENVIRONMENT_VARIABLES as LION_BOOTSTRAP_CONFIG
logging.info(f"Loaded LION_BOOTSTRAP_CONFIG: {len(LION_BOOTSTRAP_CONFIG)} items.")
logging.info(f"LION_USER: {LION_BOOTSTRAP_CONFIG.get('LION_USER_FULL_NAME', 'NOT SET')}")