# Use an official Python runtime as a parent image
FROM arm64v8/python:3

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

RUN pip install asyncio
RUN pip install numpy
RUN pip install fastapi
RUN pip install minimalmodbus
RUN pip install uvicorn
RUN pip install pyserial
RUN pip install python-statemachine
RUN pip install transitions

# Run app.py when the container launches
CMD ["python", "reterminal_backend_v_1_1.py"]
