FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    requests \
    psycopg2-binary

COPY keitaro_sync.py .

CMD ["python", "-u", "keitaro_sync.py"]
