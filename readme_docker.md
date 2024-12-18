
### Dockerfile

```Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY docker .

# If you have a .env file, you can copy it as well:
# COPY .env ./

# Expose no ports by default since this is a subscriber, not a server
# EXPOSE <port> # Not strictly necessary since this service connects to a broker, does not listen.

# Set environment variables as needed
# You may rely on .env or pass these via docker run -e
ENV PYTHONUNBUFFERED=1

# Run the application
CMD [ "python", "app.py" ]
```

---

### README_DOCKER.md

```markdown
# Running the MQTT Error Reporting Service in Docker

This document explains how to build and run the MQTT Error Reporting service inside a Docker container.

## Prerequisites

- Docker installed on your system: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- Access to a running MQTT broker (e.g., Mosquitto) reachable from within the container.

## Building the Docker Image

From the project root directory (where the `Dockerfile` resides), run:

```bash
docker build -t error-reporting-app:latest .
```

This command:
- Uses the provided `Dockerfile` to create an image named `error-reporting-app` with the `latest` tag.
- Installs all required dependencies based on `requirements.txt`.
- Copies the application source code into the image.

## Running the Container

Once built, you can run the container:

```bash
docker run \
    -it \
    --rm \
    --name error-reporting-service \
    -v $(pwd)/.test_data:/.test_data \
    -e MQTT_HOST=broker_host \
    -e MQTT_PORT=1883 \
    -e ERROR_REPORT_FOLDER=/.test_data \
    -e ALLOWED_APP_NAME="sweet-spot, weather-station, web_app" \
    -e TOPIC="/alerts/error-reporting" \
    -e ALLOW_ANONYMOUS=true \
    -e DEAD_LETTER_APP_NAME=".dead-letter" \
    -e APP_LOG_LEVEL="DEBUG" \
    -e ERROR_REPORTING_APP_NAME="error-reporting-app" \
    -e MAX_RETRIES_ON_EXCEPTION=-1 \
    -e RESTART_DELAY_ON_EXCEPTION=5 \
    error-reporting-app:latest
```

**Explanation of Flags:**

- `-it`: Runs the container in interactive mode with a pseudo-TTY.
- `--rm`: Automatically remove the container when it exits.
- `--name error-reporting-service`: Names the running container.  
- `-v $(pwd)/.test_data:/.test_data`: Mounts a local directory for storing error reports. Adjust this to your environment.  
- `-e MQTT_HOST=broker_host`: Example environment variable injection. Replace `broker_host` with the actual MQTT broker hostname or IP.
- `-e [...]`: Additional environment variables as needed.  
- `error-reporting-app:latest`: The image name and tag.

If you have a `.env` file, you can place it in the image during build (not recommended for sensitive credentials) or simply mount it at runtime:

```bash
docker run \
    -it \
    --rm \
    -v $(pwd)/.env:/app/.env \
    -v $(pwd)/.test_data:/.test_data \
    error-reporting-app:latest
```

**Note:** For sensitive information like usernames/passwords, it’s often better to pass them as environment variables using `-e` flags rather than baking them into the image.

## Testing with the Test Publisher

You can run the test publisher script in a separate container to send test messages to the broker:

```bash
docker run \
    -it \
    --rm \
    --name test-publisher \
    -e MQTT_HOST=broker_host \
    -e MQTT_PORT=1883 \
    -e MQTT_KEEPALIVE=60 \
    -e TOPIC="/alerts/error-reporting" \
    error-reporting-app:latest \
    python test_publisher.py
```

This will:
- Start another container using the same image.
- Execute `python test_publisher.py` inside it.
- Publish test messages to the specified MQTT topic.

## Logs

Check logs of the main container using:

```bash
docker logs -f error-reporting-service
```

This lets you see real-time log messages, verifying that the service is receiving and processing messages as intended.

## Stopping the Service

To stop the containerized service, run:

```bash
docker stop error-reporting-service
```

This will terminate the container and, because we used `--rm`, the container is removed as well.

## Additional Notes

- The Docker image uses Python's slim base image to keep the footprint small.
- To customize behavior further, adjust the Dockerfile or environment variables as needed.
- For production scenarios, consider using Docker Compose or Kubernetes for deploying the broker, the service, and test publisher together.
