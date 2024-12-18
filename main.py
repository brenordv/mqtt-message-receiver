import json
import re
import time
import traceback
from datetime import datetime

import paho.mqtt.client as mqtt

from config import DEAD_LETTER_APP_NAME, ALLOWED_APP_NAMES, ERROR_REPORT_FOLDER, TOPIC, APP_LOG_LEVEL, LOGGER, \
    MQTT_USERNAME, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE, ERROR_REPORTING_APP_NAME, \
    MAX_RETRIES_ON_EXCEPTION, RESTART_DELAY_ON_EXCEPTION

retry_count = 0


def _sanitize_folder_name(name: str) -> str:
    """
    Removes or substitutes characters not suitable for folder names.
    This regex removes all characters except letters, numbers, underscores, and hyphens.
    """
    LOGGER.debug(f"Sanitizing folder name: {name}")
    return re.sub(r"[^a-zA-Z0-9_\-.]", "_", name).lower().strip()


def _validate_message_schema(msg: dict) -> bool:
    """
    Validate the schema of the incoming message.
    Required fields: app_name (str), error_message (str)
    Optional fields: stack_trace (str) defaulting if missing
    """
    LOGGER.debug(f"Validating message schema: {msg}")
    if not isinstance(msg, dict):
        LOGGER.error("Message is not a dictionary.")
        return False

    if "app_name" not in msg or not isinstance(msg["app_name"], str):
        LOGGER.error("Missing or invalid app_name field.")
        return False

    if msg["app_name"].strip().lower() not in ALLOWED_APP_NAMES:
        LOGGER.error("App name not allowed.")
        return False

    if "error_message" not in msg or not isinstance(msg["error_message"], str):
        LOGGER.error("Missing or invalid error_message field.")
        return False

    # stack_trace is optional
    LOGGER.info("Message schema is valid.")
    return True


def process_message(msg_dict: dict):
    """
    Process a valid or invalid message. If invalid or app_name not allowed, will treat as dead letter.
    Otherwise, create a file inside the app folder.
    """
    LOGGER.debug(f"Processing message: {msg_dict}")

    # Determine if it's valid and allowed
    is_valid = _validate_message_schema(msg_dict)
    original_app_name = msg_dict["app_name"]
    app_name = msg_dict["app_name"] if is_valid else DEAD_LETTER_APP_NAME

    if app_name == DEAD_LETTER_APP_NAME:
        LOGGER.warning("Message treated as dead letter.")

    # Get fields or set defaults
    error_message = msg_dict.get("error_message", "No error message provided")
    stack_trace = msg_dict.get("stack_trace", "No Stack-trace provided")

    # Sanitize folder name
    sanitized_app_name = _sanitize_folder_name(app_name)

    app_path = ERROR_REPORT_FOLDER.joinpath(sanitized_app_name)
    app_path.mkdir(parents=True, exist_ok=True)

    # Prepare filename with the pattern: YYYY-MM-DD--HH-MM-SS--fff.txt
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d--%H-%M-%S--%f.txt")
    file_path = app_path.joinpath(filename)

    LOGGER.debug(f"Writing report to file: {file_path}")

    # Format the content
    incident_date_str = now.strftime("%Y/%m/%d %H:%M:%S.%f")
    content = (
        f"App Name: {original_app_name}\n"
        f"Incident date: {incident_date_str}\n"
        f"------------------------------------------------------\n"
        f"Error:\n{error_message}\n"
        f"------------------------------------------------------\n"
        f"Stack trace:\n{stack_trace}\n"
    )

    # Write the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        LOGGER.info(f"Connected to MQTT broker successfully. Subscribing to topic: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        LOGGER.error(f"Failed to connect to MQTT broker. Return code {rc}")

    LOGGER.debug(f"Connection params: [host: {client._host}:{client._port}][userdata: {userdata}][flags: {flags}]")


def on_message(client, userdata, msg):
    payload_str = ""
    try:
        payload_str = msg.payload.decode("utf-8")
        msg_dict = json.loads(payload_str)
        LOGGER.debug(f"Received message: {msg_dict}")
    except (ValueError, json.JSONDecodeError) as e:
        err_msg = f"Could not decode JSON payload: {payload_str}. [Error: {e}][Client: {client._host}:{client._port}][Userdata: {userdata}]"
        LOGGER.error(err_msg)
        msg_dict = {
            "app_name": DEAD_LETTER_APP_NAME,
            "error_message": f"{err_msg}\nPayload as text:\n{payload_str}",
            "stack_trace": traceback.format_exc()
        }

    process_message(msg_dict)


def main():
    global retry_count
    try:
        LOGGER.info("Starting error reporting service...")
        client = mqtt.Client()

        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        else:
            LOGGER.info("Using anonymous connection to MQTT broker.")

        client.on_connect = on_connect
        client.on_message = on_message

        LOGGER.info(f"Connecting to MQTT broker: {MQTT_HOST}:{MQTT_PORT} [{MQTT_KEEPALIVE}s]")
        client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)

        LOGGER.info("Starting MQTT loop...")
        client.loop_forever()
    except Exception as e:
        LOGGER.error(f"Unexpected error occurred: {e}")
        LOGGER.debug(traceback.format_exc())
        process_message({
            "app_name": ERROR_REPORTING_APP_NAME,
            "error_message": f"Unexpected error occurred: {e}",
            "stack_trace": traceback.format_exc()
        })

        retry_count += 1
        if retry_count > MAX_RETRIES_ON_EXCEPTION != -1:
            LOGGER.error("Max retries reached. Exiting...")
            return

        LOGGER.info(f"Restarting in {RESTART_DELAY_ON_EXCEPTION} seconds...")
        time.sleep(RESTART_DELAY_ON_EXCEPTION)

        main()


if __name__ == "__main__":
    main()
