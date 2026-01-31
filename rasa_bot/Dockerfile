# rasa_bot/Dockerfile
# action_server
FROM rasa/rasa-sdk:3.6.2

USER root
WORKDIR /app

# 1. Copy everything from the rasa_bot folder
COPY . .

# 2. DEBUG: This will list your files in the logs so we can see the truth
RUN ls -la

# 3. Install requirements
# We use a safety check to make sure the file is actually there
RUN pip install --no-cache-dir -r requirements.txt

USER 1001

# Start the action server
CMD ["start", "--actions", "actions", "--port", "5055"]
