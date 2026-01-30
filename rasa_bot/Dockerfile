# rasa_bot/Dockerfile
# action_server
FROM rasa/rasa-sdk:3.6.2

USER root
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actions folder
COPY ./actions /app/actions

USER 1001

# Start the action server on the port Railway provides
CMD ["start", "--actions", "actions", "--port", "5055"]