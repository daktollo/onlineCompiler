from pymongo import MongoClient

try:
    client = MongoClient("mongodb://admin:password@localhost:27017/", serverSelectionTimeoutMS=5000)
    print(client.server_info())  # Bağlantıyı doğrular
    print("Bağlantı başarılı")
except Exception as e:
    print("Bağlantı başarısız:", e)
