
from os import startfile
from pathlib import Path
from subprocess import CalledProcessError, run, CompletedProcess

from lion.config.paths import LION_PROJECT_HOME
from lion.logger.exception_logger import log_exception
from lion.maintenance.process_manager import toggle_processes


def reboot_app():

    toggle_processes(is_redundant=True)
    errmsg = ''
    try:
        if (LION_PROJECT_HOME / 'start_lion.vbs').exists():

            wscript_path = Path("C:\\Windows\\System32\\wscript.exe")
            lion_executable = Path('start_lion.vbs').resolve()

            if wscript_path.exists():
                lion_executable = wscript_path.resolve()
                startfile(str(LION_PROJECT_HOME / 'start_lion.vbs'))
            else:
                raise FileNotFoundError(f'rebooting failed due to missing wscript.exe')

        elif (LION_PROJECT_HOME / 'start_lion.bat').exists():
            lion_executable = Path('start_lion.bat').resolve()

            completed_process: CompletedProcess = run(str(lion_executable), shell=True, check=True)
            if completed_process.returncode != 0:
                raise CalledProcessError(completed_process.returncode, lion_executable)
        else:
            raise FileNotFoundError(f'rebooting failed due to missing start_lion.bat')

    except CalledProcessError as e:
        errmsg = f'rebooting failed due to CalledProcessError! {str(e)}'

    except Exception:
        errmsg = log_exception(popup=False, remarks='Rebooting failed due to error.', level='error')
        
    
    if errmsg:
        return {'code': 400, 'message': f'{errmsg}'}
