FROM python:3.14-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV STATE_DIR=/state \
    CALIBRE_LIBRARY_PATH=/books \
    CALIBRE_DB_FILENAME=metadata.db \
    HTTP_PORT=9002

EXPOSE 9002

CMD ["python3", "-m", "kindle_send_mcp.server"]
