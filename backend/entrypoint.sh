#!/bin/bash

# Run the seed script
echo "Running database seeding..."
python seed.py

# Then start the actual FastAPI server
echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
