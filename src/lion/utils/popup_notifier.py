import logging
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER

def show_popup(message='', mytitle=''):

    try:
        logging.info(f"{mytitle}: {message}")
        STATUS_CONTROLLER.POPUP_MESSAGE = f"{mytitle}: {message}" if mytitle else message
    
    except Exception as err:
        logging.error(f"Error in show_popup: {str(err)}")
        STATUS_CONTROLLER.POPUP_MESSAGE = f"Error in show_popup: {str(err)}"

def show_error(message):
    show_popup(message=message, mytitle='ERROR')
