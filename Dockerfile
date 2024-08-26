# Use the official Python 3.9 slim image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install the necessary Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    asyncio \
    numpy \
    minimalmodbus \
    pyserial \
    python-statemachine \
    transitions \
    websockets \
    httpx

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "app/reterminal_backend_v_1_1.py"]
