# rasa_bot/Dockerfile
# action_server

# FROM rasa/rasa-sdk:3.6.2

# USER root
# WORKDIR /app

# # Copy requirements from rasa_bot/requirements.txt
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the actions folder from rasa_bot/actions/
# COPY ./actions /app/actions

# USER 1001

# # Listen on 5055 (Rasa default)
# CMD ["start", "--actions", "actions", "--port", "5055"]


FROM rasa/rasa-sdk:3.6.2

USER root
WORKDIR /app

# Copy requirements from rasa_bot/requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actions folder from rasa_bot/actions/
COPY ./actions /app/actions

USER 1001

# Listen on 5055 (Rasa default)
CMD ["start", "--actions", "actions", "--port", "8080"]
