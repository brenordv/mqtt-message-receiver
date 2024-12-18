# MQTT Error Reporting Service

This Python application continuously listens to an MQTT topic (defined in `.env` as `TOPIC`) for incoming error reports.
It validates the incoming messages, stores them in a time-stamped file structure if valid and allowed, or routes them to
a `dead-letter` folder if they fail validation or are not permitted.

## How It Works
1. **Connect to MQTT Broker:**  
The application connects to an MQTT broker using credentials and configuration specified in the `.env` file.

2. **Listen to a Topic:**  
It subscribes to the specified `TOPIC` (e.g., `/alerts/error-reporting`) to receive JSON-formatted messages.

3. **Validate Messages:**  
Messages must have:  
- `app_name`: string (required, must be in `ALLOWED_APP_NAME`)  
- `error_message`: string (required)  
- `stack_trace`: string (optional, defaults to "No Stack-trace provided")

If any required field is missing or invalid, or if `app_name` is not allowed, the message is treated as a dead letter.

4. **Store Reports:**  
Valid reports are written to:  
`<ERROR_REPORT_FOLDER>/<app_name>/YYYY-MM-DD--HH-MM-SS--fff.txt`  

Dead letters are written to:  
`<ERROR_REPORT_FOLDER>/.dead-letter/…`

Each file contains a formatted error report, including incident date and detailed stack trace if provided.

5. **Error Handling & Retries:**  
On unexpected exceptions, the service logs the error, writes an error report for debugging, and may attempt to restart 
based on configuration (`MAX_RETRIES_ON_EXCEPTION`, `RESTART_DELAY_ON_EXCEPTION`).

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_KEEPALIVE=60
MQTT_USERNAME=user
MQTT_PASSWORD=password
ERROR_REPORT_FOLDER=.test_data
ALLOWED_APP_NAME=sweet-spot, weather-station, web_app
TOPIC=/alerts/error-reporting
ALLOW_ANONYMOUS=true
DEAD_LETTER_APP_NAME=.dead-letter
APP_LOG_LEVEL=DEBUG
ERROR_REPORTING_APP_NAME=error-reporting-app
MAX_RETRIES_ON_EXCEPTION=-1
RESTART_DELAY_ON_EXCEPTION=5
```

**Notes:**
- `MQTT_HOST` and `MQTT_PORT`: Address and port of your MQTT broker.
- `MQTT_KEEPALIVE`: Interval in seconds for the keepalive protocol.
- `ERROR_REPORT_FOLDER`: Base directory for storing reports.  
- `ALLOWED_APP_NAME`: Comma-separated list of allowed `app_name` values.
- `TOPIC`: MQTT topic to subscribe to.
- `ALLOW_ANONYMOUS`: If `true`, connects to MQTT without username/password (if not set).
- `DEAD_LETTER_APP_NAME`: Name of the "application" folder for dead letters.
- `APP_LOG_LEVEL`: Logging level (e.g., `DEBUG`, `INFO`, `ERROR`).
- `ERROR_REPORTING_APP_NAME`: The app name used when reporting internal errors.
- `MAX_RETRIES_ON_EXCEPTION`: How many times to retry connecting on exceptions (`-1` means infinite retries).
- `RESTART_DELAY_ON_EXCEPTION`: How many seconds to wait before restarting the main loop after an error.

## Requirements

- Python 3.7+ (I'm using 3.13.1)
- MQTT Broker (e.g. [Eclipse Mosquitto](https://mosquitto.org/))

### Install dependencies globally
You can install the dependencies globally by running the following command:
```bash
pip install -r requirements.txt
```

### Install dependencies in a virtual environment
You can also install the dependencies in a virtual environment by running the following commands:
```bash
pip install virtualenv
virtualenv venv
venv/bin/activate
pip install -r requirements.txt
```

## Running the Service
To start the main error reporting service:

```bash
python main.py
```

If the connection is successful, you should see log messages indicating a successful subscription to the configured MQTT
topic.

When messages arrive on the `TOPIC`, they are processed as described above. Valid and allowed messages are stored under
their `app_name` folder, invalid or unauthorized messages end up in the `.dead-letter` folder.

# Testing with the Test Publisher Script
A `test_publisher.py` script is provided to help you test this service. The script publishes a series of test messages, 
each of which tests a different scenario (valid message, invalid schema, unauthorized app_name, etc.), at a fixed 
interval.

### Usage
Run the test publisher as:
```bash
python test_publisher.py
```

**What It Does:**

- Connects to the same MQTT broker as the main app (based on `.env` settings).
- Publishes a series of predefined messages to the `TOPIC` every `PUBLISH_INTERVAL` seconds.
- Cycles through a set of test messages:
  - A valid message with allowed `app_name`
  - A message with an unauthorized `app_name`
  - Messages missing required fields
  - Messages with incorrect field types

This helps verify the main application's behavior when processing different kinds of input.

### Example Output

For a valid message scenario:
```json
{
  "app_name": "web_app",
  "error_message": "Encountered a critical error in module X",
  "stack_trace": "Exception: NullPointerException at line 42"
}
```
You should see a new file generated in `.test_data/web_app/` with a timestamped filename, containing the formatted 
incident report.

For invalid or unauthorized messages, you should see files appear in `.test_data/.dead-letter/` instead.

## Troubleshooting

- **Cannot connect to MQTT broker:**  
Check the broker is running and that `MQTT_HOST` and `MQTT_PORT` are correct in `.env`. If authentication is required, 
ensure `MQTT_USERNAME` and `MQTT_PASSWORD` are set in your `config.py` or `.env` as appropriate.

- **No files appearing:**  
Check the logs for validation errors or other issues. Ensure that `ERROR_REPORT_FOLDER` exists and is writable, and that
messages follow the required schema.

- **Infinite retries on exceptions:**  
If `MAX_RETRIES_ON_EXCEPTION` is set to `-1`, the app will continuously attempt to restart after failures. To limit 
retries, change this value in `.env`.
