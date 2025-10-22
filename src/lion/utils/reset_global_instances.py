def reset_all():

    from lion.delta_suite.delta_logger import DELTA_LOGGER
    from lion.algorithms.depth_first_search import DEPTH_FIRST_SEARCH
    from lion.optimization.optimization_logger import OPT_LOGGER
    from lion.ui.driver_ui import DRIVERS_UI
    from lion.movement.movements_manager import UI_MOVEMENTS
    from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
    from lion.shift_data.shift_data import UI_SHIFT_DATA
    from lion.tour.tour_analysis import UI_TOUR_ANALYSIS

    UI_SHIFT_DATA.reset()
    UI_MOVEMENTS.reset()
    DEPTH_FIRST_SEARCH.reset()
    DRIVERS_UI.reset()
    UI_RUNTIMES_MILEAGES.reset()
    UI_TOUR_ANALYSIS.reset()
    DELTA_LOGGER.reset()
    OPT_LOGGER.reset()
