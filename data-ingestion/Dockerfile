FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/data_ingestion.py /app/

RUN pip install --no-cache-dir \
    requests>=2.28 \
    google-api-python-client>=2.0 \
    google-auth>=2.0

ENV DRIVE_FOLDER_ID="" \
    GOOGLE_CRED_B64=""

ENTRYPOINT ["python", "/app/data_ingestion.py"]
