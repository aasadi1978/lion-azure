import logging
import re
import subprocess
import platform
from lion.create_flask_app.create_app import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception
    

class PIDManager(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'pid_manager'

    pid = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True)
    process_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(100), unique=True, nullable=False)
    is_redundant = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, default=False, nullable=False)
    is_main = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, default=False, nullable=False)

    def __init__(self, kwargs):
        self.pid = kwargs['pid']
        self.process_name = kwargs.get('process_name', 'python-lion-' + str(kwargs['pid']))
        self.is_redundant = kwargs.get('is_redundant', False)
        self.is_main = kwargs.get('is_main', False)
    
    @classmethod
    def register_pid(cls, pid: int, **kwargs):

        existing = cls.query.filter_by(pid=pid).first()
        if existing:
            LION_SQLALCHEMY_DB.session.delete(existing)
            LION_SQLALCHEMY_DB.session.commit()

        new_pid = cls({'pid': pid, 
                       'process_name': kwargs.get("process_name", 'lion-python-' + str(pid)), 
                       'is_redundant': kwargs.get("is_redundant", False),
                       'is_main': 'py-lion-main' in kwargs.get("process_name", '').lower()})
        
        LION_SQLALCHEMY_DB.session.add(new_pid)
        LION_SQLALCHEMY_DB.session.commit()
        return new_pid

    @classmethod
    def clear_all(cls):
        try:
            num_rows_deleted = cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()
            return num_rows_deleted
        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.error(f"Error clearing PIDManager table: {e}")
            return 0
    
    @classmethod
    def mark_redundant(cls, pid: int):
        try:
            pid_entry = cls.query.filter_by(pid=pid).first()
            if pid_entry:
                pid_entry.is_redundant = True
                LION_SQLALCHEMY_DB.session.commit()
                return True
            return False
        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            logging.error(f"Error marking PID {pid} as redundant: {e}")
            return False
    
    @classmethod
    def get_all(cls):
        try:
            return cls.query.all()
        except Exception as e:
            logging.error(f"Error retrieving all PIDs: {e}")
            return []
        
    @classmethod
    def clean_up(cls):

        """Remove entries for PIDs that are no longer running."""
        try:
            live_sessions = cls.get_running_sessions()
            all_pids = [pid for (pid,) in cls.query.with_entities(cls.pid).all()]

            for pid in all_pids:
                if pid not in live_sessions:
                    cls.query.filter_by(pid=pid).delete()
                    LION_SQLALCHEMY_DB.session.commit()

                    logging.info(f"Cleaned up stale PID entry: {pid}")
        
        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception("clean up PIDs failed.")

    @classmethod
    def kill_main_processes(cls):

        cls.clean_up()
        main_pids = [pid for (pid,) in cls.query.with_entities(cls.pid).filter(cls.is_main).all()]
        if not main_pids:
            return
        
        for pid in main_pids:

            try:
                if cls.kill_pid(pid):
                    logging.info(f"Killed main PID {pid}")
                    cls.query.filter_by(pid=pid).delete()
                    LION_SQLALCHEMY_DB.session.commit()
            except Exception as e:
                LION_SQLALCHEMY_DB.session.rollback()
                log_exception("Killing main PIDs failed.")

    @classmethod
    def kill_redundant_processes(cls):

        cls.clean_up()
        redundant_pids = [pid for (pid,) in cls.query.with_entities(cls.pid).filter(cls.is_redundant).all()]
        if not redundant_pids:
            return
        
        for pid in redundant_pids:

            try:
                if cls.kill_pid(pid):
                    logging.info(f"Killed redundant PID {pid}")
                    cls.query.filter_by(pid=pid).delete()
                    LION_SQLALCHEMY_DB.session.commit()
            except Exception as e:
                LION_SQLALCHEMY_DB.session.rollback()
                log_exception("Killing redundant PIDs failed.")
    
    @classmethod
    def get_running_sessions(cls):

        if platform.system().lower() != 'windows':
            return []

        try:
            """Return a list of (pid, name) tuples for python.exe processes running on Windows."""
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            lines = result.stdout.strip().splitlines()

            pids = []
            for line in lines[3:]:  # skip header lines
                match = re.match(r'python\.exe\s+(\d+)', line)
                if match:
                    pids.append(int(match.group(1)))

            return pids
        
        except Exception as e:
            log_exception("Error retrieving python.exe PIDs failed.")
            return []
    
    @classmethod
    def kill_pid(cls, pid):
        """Force kill a process by PID."""
        try:

            if platform.system().lower() == 'windows':
                process_output: subprocess.CompletedProcess = subprocess.run(['taskkill', '/PID', str(pid), '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if process_output.returncode != 0:
                    logging.error(f"Failed to kill PID {pid}, return code: {process_output.returncode}")
                    return False

                logging.info(f"Killed PID {pid} successfully.")
            else:
                logging.info(f"Attempting to kill PID {pid} on non-Windows platform. Operation cancelled!.")
            return True
        except Exception as e:
            log_exception(f"Error killing PID {pid} failed.")
            return False
