# Python imajından türet
FROM python:3.10-slim

# Docker CLI araçlarını yükle (DinD için gerekli)
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizini ayarla
WORKDIR /coderunner

# Gereksinim dosyalarını kopyala ve kur
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ana Python dosyasını kopyala
COPY coderunner.py .

# Uygulamayı başlat
CMD ["python", "coderunner.py"]
