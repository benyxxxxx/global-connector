# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including git and other tools
RUN apt-get update && \
    apt-get install -y \
    curl \
    iputils-ping \
    git \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Configure git (required for GitPython operations)
RUN git config --global user.email "bot@example.com" && \
    git config --global user.name "Telegram Bot" && \
    git config --global init.defaultBranch main

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables for Git Python
ENV GIT_PYTHON_REFRESH=quiet

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]