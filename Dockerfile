FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

HEALTHCHECK --interval=60s --timeout=10s --retries=3 CMD python healthcheck.py

CMD [ "python", "main.py" ]