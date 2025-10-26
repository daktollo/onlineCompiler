FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY . .  # Commented out for development - using volume mount instead

EXPOSE 5000

CMD ["python", "app.py"]
