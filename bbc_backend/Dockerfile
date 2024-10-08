# Use the official Python 3.12 image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install build-essential and other necessary libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir fastai \
    && pip install --no-cache-dir scikit-image \
    && pip install --no-cache-dir fastapi[standard]

# Copy the application code
COPY api/ .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]