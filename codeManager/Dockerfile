FROM python:3.10

RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /manager

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask-cors==4.0.0

# Copy application code
COPY . .

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "codeManager.py"]

