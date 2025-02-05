# Use Python 3.11 (explicitly set version)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /evidai

# Install system dependencies required for pandas, numpy, psycopg2, and Cython
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    python3-pip \
    python3-distutils \
    python3-setuptools \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /evidai/

# Upgrade pip, setuptools, and wheel before installing dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy the entire project into the container
COPY . /evidai/

# Expose the port the app runs on
EXPOSE 8000

# Start the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "evidai.wsgi:application"]
