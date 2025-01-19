LABEL org.opencontainers.image.source https://github.com/elAgala/departamentos_bot

# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files into the container
COPY . .

# Copy the run.sh script into the container
COPY run.sh .

# Set the entrypoint to run the run.sh script
ENTRYPOINT ["./run.sh"]
