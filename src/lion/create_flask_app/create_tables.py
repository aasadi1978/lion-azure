import logging
from os import getenv
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
        from lion.orm.temp_changeover import TempChangeover
        from lion.orm.temp_drivers_info import TempDriversInfo
        from lion.orm.temp_scn_info import TempScnInfo
        from lion.orm.temp_shift_movement_entry import TempShiftMovementEntry

        if getenv('is_azure_sql_db_connected', 'FALSE') == 'TRUE':

            from lion.orm_azure.log_entry import LogEntry as AzureLogEntry
            from lion.orm_azure.operators import Operator
            from lion.orm_azure.vehicle_type import VehicleType
            from lion.orm_azure.pickle_dumps import PickleDumps
            from lion.orm_azure.user_params import UserParams
            from lion.orm_azure.traffic_type import TrafficType
            from lion.orm_azure.changeover import Changeover
            from lion.orm_azure.shift_movement_entry import ShiftMovementEntry
            from lion.orm_azure.drivers_info import DriversInfo
            from lion.orm_azure.cost import Cost
            from lion.orm_azure.orm_runtimes_mileages import RuntimesMileages
            from lion.orm_azure.driver_report import DriverReport
            from lion.orm_azure.location_mapping import LocationMapper as AzureLocationMapper
            from lion.orm_azure.location import Location
            from lion.orm_azure.opt_movements import OptMovements
            from lion.orm_azure.pickle_dumps import PickleDumps as AzurePickleDumps
            from lion.orm_azure.resources import Resources
            from lion.orm_azure.time_stamp import TimeStamp
            from lion.orm_azure.user_directory import UserDirectory
            from lion.orm_azure.user_params import UserParams as AzureUserParams
            from lion.orm_azure.log_entry import LogEntry as AzureLogEntry

        LION_SQLALCHEMY_DB.create_all()

        logging.debug("All tables created successfully (if they did not already exist).")