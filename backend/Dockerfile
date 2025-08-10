# Base image using Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the backend port (default 8080)
EXPOSE 8080

# Start the application using the provided start script
CMD ["/bin/sh", "start.sh"]
