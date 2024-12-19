import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from simple_log_factory.log_factory import log_factory

# Load environment variables from .env file
load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))

ALLOW_ANONYMOUS = os.getenv("ALLOW_ANONYMOUS", False).lower().strip() == "true"

TOPIC = os.getenv("TOPIC")

DEAD_LETTER_APP_NAME = os.getenv("DEAD_LETTER_APP_NAME", ".dead-letter")

APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")
LOGGER: logging = log_factory("error-reporting", log_level=APP_LOG_LEVEL, unique_handler_types=True)

ERROR_REPORTING_APP_NAME = os.getenv("ERROR_REPORTING_APP_NAME", "error-reporting-app")

MAX_RETRIES_ON_EXCEPTION = int(os.getenv("MAX_RETRIES_ON_EXCEPTION", -1))
RESTART_DELAY_ON_EXCEPTION = int(os.getenv("RESTART_DELAY_ON_EXCEPTION", 5))

_error_report_folder = os.getenv("ERROR_REPORT_FOLDER")

ALLOWED_APP_NAMES = list(set(
    [name.strip().lower() for name in os.getenv("ALLOWED_APP_NAME", "").split(",") if name.strip()]
))
ALLOWED_APP_NAMES.append(ERROR_REPORTING_APP_NAME)

_errors = []
# DEAD_LETTER_APP_NAME is required, but it as a default value.
_required_variables = {
    "MQTT_HOST": MQTT_HOST,
    "MQTT_PORT": MQTT_PORT,
    "TOPIC": TOPIC,
    "MQTT_KEEPALIVE": MQTT_KEEPALIVE,
    "ERROR_REPORT_FOLDER": _error_report_folder
}

if not ALLOW_ANONYMOUS and any([value is None for value in [MQTT_USERNAME, MQTT_PASSWORD]]):
    _errors.append("MQTT_USERNAME and MQTT_PASSWORD must be set if ALLOW_ANONYMOUS is false")

for var_name, var_value in _required_variables.items():
    if var_value is not None:
        continue

    _errors.append(f"Required variable {var_name} not set in .env file")

if len(ALLOWED_APP_NAMES) == 0:
    _errors.append("No allowed app names set in .env file. Everything would be treated as dead letter.")

_must_be_above_zero = [MQTT_PORT, MQTT_KEEPALIVE]
for var in _must_be_above_zero:
    if var <= 0:
        _errors.append(f"{var} must be greater than 0")

if len(_errors) > 0:
    raise ValueError("\n".join(_errors))

ERROR_REPORT_FOLDER = Path(_error_report_folder)
ERROR_REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
