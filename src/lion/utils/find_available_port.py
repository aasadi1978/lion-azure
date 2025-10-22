from os import environ, getenv
import logging
from socket import AF_INET, SOCK_STREAM, error, socket

def locate_free_port(start_port=2000, end_port=10000):

    for port in range(start_port, end_port):
        with socket(AF_INET, SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except error:
                logging.warning(f"Port {port} is unavailable. Searching for another port ...")
            except Exception as e:
                logging.warning(f"Port {port} is unavailable. Reason: {e}. Searching for another port ...")
                continue
    return None

def get_port():
    """
    Attempts to bind to port 8080 on all interfaces and returns the port number if successful.
    If port 8080 is unavailable, calls `locate_free_port()` to find and return a free port.
    Returns None if not running as the main Werkzeug process.
    Returns:
        int or None: The available port number, or None if not running as the main process.
    """

    if getenv('LION_DEBUG_MODE').upper() == 'TRUE':
        if not str(environ.get("WERKZEUG_RUN_MAIN")) != "true":
            logging.warning("Not running as the main Werkzeug process.")
            # return None

    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", 8080))
        except error:
            logging.warning(f"Port 8080 is unavailable. Searching for another port ...")

        except Exception as e:
            logging.warning(f"Port 8080 is unavailable. Reason: {e}. Searching for another port ...")
            return locate_free_port()
        
        return 8080
