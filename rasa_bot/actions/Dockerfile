FROM rasa/rasa-sdk:3.6.2

# Switch to root user to install dependencies
USER root

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Switch back to a non-root user (Rasa default user 1001)
USER 1001