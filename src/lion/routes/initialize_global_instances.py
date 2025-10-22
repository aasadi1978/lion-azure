import logging
from flask import Flask

def initialize_all(app: Flask):

    with app.app_context():

        from lion.delta_suite.delta_logger import DELTA_LOGGER
        from lion.algorithms.depth_first_search import DEPTH_FIRST_SEARCH
        from lion.optimization.optimization_logger import OPT_LOGGER
        from lion.ui.driver_ui import DRIVERS_UI
        from lion.movement.movements_manager import UI_MOVEMENTS
        from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
        from lion.shift_data.shift_data import UI_SHIFT_DATA
        from lion.tour.tour_analysis import UI_TOUR_ANALYSIS
        from lion.ui.ui_params import UI_PARAMS

        try:
            UI_PARAMS.initialize()
            UI_SHIFT_DATA.initialize()
            UI_MOVEMENTS.initialize()
            DEPTH_FIRST_SEARCH.initialize()
            DRIVERS_UI.initialize()
            UI_RUNTIMES_MILEAGES.initialize()
            UI_TOUR_ANALYSIS.initialize()
            DELTA_LOGGER.reset()
            OPT_LOGGER.reset()

            logging.info(f"Initializing global singletons for {app.name} completed successfully.")
        except Exception as e:
            logging.critical(f'Error during global instances initialization: {e}')
