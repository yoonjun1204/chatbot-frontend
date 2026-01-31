# rasa_bot/Dockerfile
# action_server
FROM rasa/rasa-sdk:3.6.2

USER root
WORKDIR /app

# Copy everything from the root directory (rasa_bot)
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure we are on the right user for Rasa
USER 1001

# Start the action server
# Rasa SDK automatically looks for a folder named "actions" or "action" 
# inside the current directory if you tell it where to look.
CMD ["start", "--actions", "actions", "--port", "5055"]
