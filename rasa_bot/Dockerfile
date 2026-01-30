FROM rasa/rasa-sdk:3.6.2

USER root

# Copy requirements from the context (rasa_bot folder)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actions folder into the container
COPY ./actions /app/actions

USER 1001