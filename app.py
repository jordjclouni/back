from flask import Flask, send_from_directory, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os

# Инициализация приложения Flask
app = Flask(__name__)

# Настройка CORS (поддержка кук + все origins или настрой конкретный)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Конфигурация базы данных и сессий
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///crossbooking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = "your-secret-key-here"
app.config['UPLOAD_FOLDER'] = 'uploads/avatars'

# Инициализация базы и миграций
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Путь к папке frontend/dist
dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))

# Маршрут: установка куки
@app.route("/set-cookie")
def set_cookie():
    response = make_response(jsonify({"message": "Cookie установлено"}))
    response.set_cookie(
        "session_id",
        "secure_cookie_value",
        secure=True,
        httponly=True,
        samesite="None"
    )
    return response

# Простой API
@app.route("/api/data")
def get_data():
    return jsonify({"message": "Это данные с сервера"})

# Обработка всех маршрутов и отдача фронта
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static_files(path):
    file_path = os.path.join(dist_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(dist_folder, path)
    else:
        return send_from_directory(dist_folder, "index.html")

# Импорт маршрутов (после инициализации app)
try:
    from routes import *  # Подключение кастомных API маршрутов
except ImportError as e:
    print(f"Ошибка импорта routes: {e}")

# Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
