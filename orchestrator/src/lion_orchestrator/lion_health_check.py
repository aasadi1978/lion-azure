import requests
import logging

url = "http://localhost:8080/health-check"

def check_health() -> bool:
    try:
        response = requests.get(url, timeout=5)  # timeout to avoid hanging
        if response.status_code == 200:
            return True
        else:
            logging.warning("Unexpected status code: %d", response.status_code)
    except requests.exceptions.RequestException as e:
        logging.error("Health check failed: %s", e)
    except Exception as e:
        logging.error("Unexpected error during health check: %s", e)
    finally:
        logging.info("Health check completed.")
        logging.info("Health check result: %s", "Success" if response.status_code == 200 else "Failure")
        
    return False