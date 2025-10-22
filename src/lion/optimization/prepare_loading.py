
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.ui.ui_params import UI_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA


def prepare_ui():
    
    UI_PARAMS.DICT_DRIVERS_PER_PAGE = {}
    UI_MOVEMENTS.reset()
    UI_SHIFT_DATA.reset()

        # if not self.load_movements_object():
        #     OPT_LOGGER.log_info(
        #         message='load_movements_object has failed!')
