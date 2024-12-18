import sys
import paho.mqtt.client as mqtt

from config import MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE

client = mqtt.Client()
try:
    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
    client.disconnect()
    sys.exit(0)

except Exception:
    sys.exit(1)
