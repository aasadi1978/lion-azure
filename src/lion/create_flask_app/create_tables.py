import logging
from flask import Flask
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB

"""
In this module, we define a function to create all database tables. For those already setup, it will skip them gracefully.
This makes it easy to ensure that all necessary tables are created without causing errors for existing ones or errors caused by
missing new tables.
"""
def create_all(app: Flask):
    
    with app.app_context():
        from lion.maintenance.pid_manager import PIDManager
        from lion.logger.log_entry import LogEntry
        from lion.orm.location_mapping import LocationMapper
        from lion.runtimes.orm_runtimes_mileages import RuntimesMileages
        from lion.orm.temp_changeover import TempChangeover, AzureChangeover
        from lion.orm.temp_drivers_info import TempDriversInfo, AzureDriversInfo
        from lion.orm.temp_scn_info import TempScnInfo, AzureScnInfo
        from lion.orm.temp_shift_movement_entry import TempShiftMovementEntry, AzureShiftMovementEntry

        LION_SQLALCHEMY_DB.create_all()

        logging.debug("All tables created successfully (if they did not already exist).")