import time
import json
import signal
import sys
from typing import Union

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client

from config import LOGGER, MQTT_USERNAME, MQTT_PASSWORD, MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE, TOPIC

# Interval in seconds between published messages
PUBLISH_INTERVAL = 5  # Adjust as needed
_mqtt_client: Union[Client, None] = None
_test_messages = {
    "Valid message, allowed app name": {
        "app_name": "web_app",
        "error_message": "Encountered a critical error in module X",
        "stack_trace": "Exception: NullPointerException at line 42"
    },
    "[dead letter] Valid message but not allowed app name": {
        "app_name": "unlisted_app",
        "error_message": "Database timeout error",
        "stack_trace": "TimeoutError at query execution"
    },
    "[dead letter] Invalid schema: Missing required fields (no app_name)": {
        "error_message": "Missing app_name here"
    },
    "[dead letter] Invalid schema: app_name not string": {
        "app_name": 1234,
        "error_message": "Type error in app_name"
    },
    "[dead letter] Invalid schema: error_message not string": {
        "app_name": "backend_service",
        "error_message": 1234
    }
}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        LOGGER.info("Test publisher connected to MQTT broker.")
    else:
        LOGGER.error(f"Failed to connect to MQTT broker. Return code {rc}")


# Graceful shutdown on Ctrl+C
def signal_handler(sig, frame):
    LOGGER.info("Shutting down test publisher...")

    if _mqtt_client is not None:
        _mqtt_client.disconnect()

    sys.exit(0)


def main() -> None:
    global _mqtt_client
    LOGGER.info("Starting test publisher...")
    _mqtt_client = mqtt.Client()

    if MQTT_USERNAME and MQTT_PASSWORD:
        _mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    else:
        LOGGER.warning("No MQTT username and password set. Connecting anonymously.")

    _mqtt_client.on_connect = on_connect
    signal.signal(signal.SIGINT, signal_handler)

    LOGGER.info(f"Connecting to MQTT broker: {MQTT_HOST}:{MQTT_PORT} [{MQTT_KEEPALIVE}s]")
    _mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)

    while True:
        for test_title, test_message in _test_messages.items():
            LOGGER.info(f"Test message: {test_title}")
            LOGGER.info(f"Message: {test_message}")
            payload_str = json.dumps(test_message)
            result = _mqtt_client.publish(TOPIC, payload_str)
            if result[0] != 0:
                LOGGER.error(f"Failed to publish message: {test_title}. Error code: {result[0]}")

            time.sleep(PUBLISH_INTERVAL)

if __name__ == '__main__':
    main()
