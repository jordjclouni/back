from app import app, db
from flask import request, jsonify, g
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from models import SafeShelf,Topic
from models import BookGenre,Genre,Author,Review,Book,UserInventory,Book, User, SafeShelf, Role, UserInventory, BookGenre, Genre
from models import User, Role
import os
import jwt
from config import SECRET_KEY, ALGORITHM
from datetime import datetime  # Правильный импорт
import random

from models import Message,Book, Author, SafeShelf, Genre, BookGenre, Review, User, Topic
import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASSWORD  # Добавьте эти переменные в config.py
import json

import datetime
import logging
from models import User, SafeShelf, Book  # Импортируйте ваши модели
from models import Book, User, SafeShelf, Role, UserInventory, BookGenre, Genre
from flask import send_from_directory
from werkzeug.utils import secure_filename

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "Backend is working!"})

# Папка для хранения аватаров
UPLOAD_FOLDER = 'uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/user/avatar', methods=['POST'])
def upload_avatar():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    if 'avatar' not in request.files:
        return jsonify({"error": "Файл аватара не передан"}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Недопустимый формат файла. Разрешены: png, jpg, jpeg, gif"}), 400

    try:
        user = User.query.get(session.get("user_id"))
        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404

        # Сохраняем файл с уникальным именем
        filename = secure_filename(f"{user.id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Обновляем URL аватара в профиле
        user.avatar_url = f"/{file_path}"
        db.session.commit()

        return jsonify({"message": "Аватар обновлён", "avatar_url": user.avatar_url}), 200
    except Exception as e:
        logger.error(f"Ошибка при загрузке аватара: {str(e)}")
        return jsonify({"error": f"Ошибка при загрузке аватара: {str(e)}"}), 500

# Маршрут для отдачи файлов аватаров
@app.route('/uploads/avatars/<filename>')
def serve_avatar(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from models import Topic, Review, User, Author  # Убедитесь, что импортируете все нужные модели
import logging

# Настройка логгера (если ещё не настроен)
logger = logging.getLogger(__name__)

# Получение книги по ID (для страницы книги)
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({"error": "Книга не найдена"}), 404

        # Получаем автора
        author = Author.query.get(book.author_id)
        # Получаем жанры
        genres = [g.genre.name for g in book.genres]
        # Получаем ячейку (если есть)
        shelf = SafeShelf.query.get(book.safe_shelf_id) if book.safe_shelf_id else None

        return jsonify({
            "id": book.id,
            "title": book.title,
            "author": {
                "id": author.id,
                "name": author.name,
                "description": author.description
            } if author else None,
            "description": book.description,
            "safe_shelf_id": book.safe_shelf_id,
            "shelf_location": {
                "id": shelf.id if shelf else None,
                "name": shelf.name if shelf else "Не указано",
                "address": shelf.address if shelf else "Не указано",
                "latitude": shelf.latitude if shelf else None,
                "longitude": shelf.longitude if shelf else None
            } if shelf else None,
            "user_id": book.user_id,
            "isbn": book.isbn,
            "status": book.status,
            "genres": genres,
            "path": book.path
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при получении книги ID {book_id}: {str(e)}")
        return jsonify({"error": f"Ошибка при получении книги: {str(e)}"}), 500
    
@app.route('/api/reviews/<int:book_id>', methods=['GET'])
def get_reviews(book_id):
    try:
        reviews = Review.query.filter_by(book_id=book_id).all()
        return jsonify([{
            "book_id": r.book_id,
            "user_id": r.user_id,
            "name": r.name,
            "text": r.text,
            "rating": r.rating
        } for r in reviews]), 200
    except Exception as e:
        logger.error(f"Ошибка при получении отзывов для книги ID {book_id}: {str(e)}")
        return jsonify({"error": f"Ошибка при получении отзывов: {str(e)}"}), 500

@app.route('/api/reviews', methods=['POST'])
def add_review():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json
    book_id = data.get("book_id")
    text = data.get("text")
    rating = data.get("rating")

    if not book_id or not text or not rating:
        return jsonify({"error": "Все поля обязательны"}), 400

    if not (1 <= rating <= 5):
        return jsonify({"error": "Рейтинг должен быть от 1 до 5"}), 400

    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({"error": "Книга не найдена"}), 404

        user = User.query.get(session.get("user_id"))
        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404

        # Проверяем, не оставлял ли пользователь уже отзыв на эту книгу
        existing_review = Review.query.filter_by(book_id=book_id, user_id=user.id).first()
        if existing_review:
            return jsonify({"error": "Вы уже оставили отзыв на эту книгу"}), 400

        new_review = Review(
            book_id=book_id,
            user_id=user.id,
            name=user.name,
            text=text,
            rating=rating
        )
        db.session.add(new_review)
        db.session.commit()

        return jsonify({"message": "Отзыв добавлен"}), 201
    except Exception as e:
        logger.error(f"Ошибка при добавлении отзыва: {str(e)}")
        return jsonify({"error": f"Ошибка при добавлении отзыва: {str(e)}"}), 500
# Получение темы и её сообщений

@app.route('/api/topic/<int:id>', methods=['GET'])
def get_topic(id):
    try:
        topic = Topic.query.get_or_404(id)
        messages = Message.query.filter_by(topic_id=id).order_by(Message.created_at.asc()).all()
        return jsonify({
            "topic": topic.to_json(),
            "messages": [message.to_json() for message in messages]
        })
    except Exception as e:
        logger.error(f"Ошибка при получении темы {id}: {str(e)}")
        return jsonify({"error": f"Ошибка при получении темы: {str(e)}"}), 500

# Создание нового сообщения в теме
@app.route('/api/topic/<int:id>/messages', methods=['POST'])
def create_message(id):
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    topic = Topic.query.get_or_404(id)
    data = request.json
    content = data.get("content")

    if not content or not content.strip():
        return jsonify({"error": "Содержимое сообщения обязательно"}), 400

    try:
        new_message = Message(
            content=content,
            topic_id=id,
            user_id=session.get("user_id")
        )
        db.session.add(new_message)
        db.session.commit()
        return jsonify({"message": "Сообщение добавлено", "id": new_message.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании сообщения в теме {id}: {str(e)}")
        return jsonify({"error": f"Ошибка при создании сообщения: {str(e)}"}), 500
        
# Получение списка тем форума
@app.route('/api/topics', methods=['GET'])
def get_topics():
    try:
        topics = Topic.query.order_by(Topic.created_at.desc()).all()
        return jsonify([topic.to_json() for topic in topics])
    except Exception as e:
        logger.error(f"Ошибка при получении тем форума: {str(e)}")
        return jsonify({"error": f"Ошибка при получении тем: {str(e)}"}), 500

# Создание новой темы
@app.route('/api/topics', methods=['POST'])
def create_topic():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json
    title = data.get("title")
    description = data.get("description")

    if not title or not description:
        return jsonify({"error": "Название и описание обязательны"}), 400

    new_topic = Topic(
        title=title,
        description=description,
        user_id=session.get("user_id")
    )
    db.session.add(new_topic)
    db.session.commit()

    return jsonify({"message": "Тема создана", "id": new_topic.id}), 201


@app.route('/api/safeshelves', methods=['GET'])
def get_safe_shelves():
    shelves = SafeShelf.query.all()
    return jsonify([
        {
            "id": shelf.id,
            "name": shelf.name,
            "address": shelf.address,
            "hours": shelf.hours,
            "description": shelf.description,
            "latitude": shelf.latitude,
            "longitude": shelf.longitude,
        }
        for shelf in shelves
    ])

@app.route('/api/safeshelves', methods=['POST'])
def add_safe_shelf():
    data = request.get_json()
    new_shelf = SafeShelf(
        name=data['name'],
        address=data['address'],
        hours=data.get('hours'),
        description=data.get('description'),
        latitude=data['latitude'],
        longitude=data['longitude']
    )
    db.session.add(new_shelf)
    db.session.commit()
    return jsonify({"message": "Safe shelf added successfully!"}), 201

@app.route('/api/safeshelves/<int:id>', methods=['PUT'])
def update_safe_shelf(id):
    # Ищем ячейку по ID
    shelf = SafeShelf.query.get(id)
    
    if shelf:
        # Если ячейка найдена, обновляем поля
        data = request.get_json()
        shelf.name = data.get('name', shelf.name)
        shelf.address = data.get('address', shelf.address)
        shelf.hours = data.get('hours', shelf.hours)
        shelf.description = data.get('description', shelf.description)
        shelf.latitude = data.get('latitude', shelf.latitude)
        shelf.longitude = data.get('longitude', shelf.longitude)

        # Сохраняем изменения
        db.session.commit()
        return jsonify({"message": "Safe shelf updated successfully!"}), 200
    else:
        # Если ячейка не найдена, создаем новую
        data = request.get_json()
        new_shelf = SafeShelf(
            name=data['name'],
            address=data['address'],
            hours=data.get('hours'),
            description=data.get('description'),
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        db.session.add(new_shelf)
        db.session.commit()
        return jsonify({"message": "Safe shelf added successfully!"}), 201

# Метод для преобразования объекта User в JSON
@property
def to_json(self):
    return {
        "id": self.id,
        "name": self.name,
        "email": self.email,
        "role_id": self.role_id
    }
User.to_json = to_json  # Добавляем метод в класс User


@app.route("/api/roles", methods=["POST"])
def add_role():
    try:
        data = request.json
        name = data.get("name")
        functions = data.get("functions")
        access_level = data.get("access_level")

        if not all([name, functions, access_level]):
            return jsonify({"error": "Все поля (name, functions, access_level) обязательны"}), 400

        # Проверяем, существует ли уже такая роль
        if Role.query.filter_by(name=name).first():
            return jsonify({"error": "Такая роль уже существует"}), 400

        new_role = Role(name=name, functions=functions, access_level=access_level)
        db.session.add(new_role)
        db.session.commit()

        return jsonify({"message": "Роль успешно добавлена", "role": new_role.to_json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/roles", methods=["GET"])
def get_roles():
    try:
        roles = Role.query.all()
        return jsonify([role.to_json() for role in roles]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
def register_user():
    try:
        data = request.json
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role_id = data.get("role_id", 2)
        avatar_url = data.get("avatar_url")
        bio = data.get("bio")
        phone = data.get("phone")
        birth_date = data.get("birth_date")

        # Приводим role_id к int
        try:
            role_id = int(role_id)
        except ValueError:
            return jsonify({"error": "Некорректный формат role_id"}), 400

        if not all([name, email, password]):
            return jsonify({"error": "Все поля (name, email, password) обязательны"}), 400

        # Проверяем права для регистрации админа
        if role_id == 1 and request.headers.get("X-Admin-Auth") != "secret_admin_key":
            return jsonify({"error": "Недостаточно прав для регистрации администратора"}), 403

        # Проверяем, существует ли такая роль
        if not Role.query.get(role_id):
            return jsonify({"error": "Некорректный role_id"}), 400

        # Проверяем, не зарегистрирован ли email уже
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email уже зарегистрирован"}), 400

        # Хэшируем пароль
        hashed_password = generate_password_hash(password)

        # Преобразуем birth_date в объект date, если он предоставлен
        from datetime import datetime
        birth_date_obj = None
        if birth_date:
            try:
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Неверный формат даты рождения (ожидается YYYY-MM-DD)"}), 400

        # Создаем нового пользователя
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role_id=role_id,
            avatar_url=avatar_url,
            bio=bio,
            phone=phone,
            birth_date=birth_date_obj
        )

        db.session.add(new_user)
        db.session.commit()

        # Формируем JSON-ответ
        user_data = {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role_id": new_user.role_id,
            "avatar_url": new_user.avatar_url,
            "bio": new_user.bio,
            "phone": new_user.phone,
            "birth_date": new_user.birth_date.isoformat() if new_user.birth_date else None
        }

        return jsonify(user_data), 201

    except ValueError as e:
        db.session.rollback()
        logger.error(f"Ошибка формата данных: {str(e)}")
        return jsonify({"error": f"Ошибка формата данных: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при регистрации: {str(e)}")
        return jsonify({"error": f"Ошибка при регистрации: {str(e)}"}), 500
    
from datetime import datetime

@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    try:
        data = request.json
        user_id = session.get("user_id")
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404

        # Обновление полей
        user.name = data.get("name", user.name)
        user.email = data.get("email", user.email)
        user.avatar_url = data.get("avatar_url", user.avatar_url)
        user.bio = data.get("bio", user.bio)
        user.phone = data.get("phone", user.phone)

        # Преобразование birth_date
        birth_date = data.get("birth_date")
        if birth_date:
            try:
                user.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Неверный формат даты рождения (ожидается YYYY-MM-DD)"}), 400

        db.session.commit()

        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "phone": user.phone,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при обновлении профиля: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Ошибка при обновлении профиля: {str(e)}"}), 500
    
@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    try:
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            user_id = int(user_id)

        logger.debug(f"Fetching user with ID: {user_id}")
        user = User.query.get(user_id)
        logger.debug(f"User object: {user} (type: {type(user)})")

        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404

        if not isinstance(user, User):
            logger.error(f"User is not a model instance: {type(user)} - {user}")
            return jsonify({"error": "Внутренняя ошибка: данные пользователя некорректны"}), 500

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "phone": user.phone,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None
        }

        return jsonify(user_data), 200
    except ValueError as e:
        logger.error(f"Некорректный user_id: {str(e)}")
        return jsonify({"error": "Некорректный идентификатор пользователя"}), 400
    except Exception as e:
        logger.error(f"Ошибка при получении профиля пользователя: {str(e)}")
        return jsonify({"error": f"Ошибка при получении профиля: {str(e)}"}), 500
    
# Получение списка пользователей
@app.route('/api/users', methods=['GET'])
def get_users():
    if not session.get("user_id") or not has_admin_role(session.get("user_id")):  # Проверка роли администратора
        return jsonify({"error": "Требуются права администратора"}), 403
    try:
        users = User.query.all()
        return jsonify([user.to_json() for user in users])
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей: {str(e)}")
        return jsonify({"error": f"Ошибка при получении пользователей: {str(e)}"}), 500

# Удаление пользователя
@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    if not session.get("user_id") or not has_admin_role(session.get("user_id")):
        return jsonify({"error": "Требуются права администратора"}), 403
    try:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Пользователь удалён"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении пользователя {id}: {str(e)}")
        return jsonify({"error": f"Ошибка при удалении пользователя: {str(e)}"}), 500

# Функция проверки роли администратора (пример)
def has_admin_role(user_id):
    user = User.query.get(user_id)
    if user and hasattr(user, 'role') and user.role and user.role.id == 1:  # Предположим, 1 — ID роли администратора
        return True
    return False

@app.route("/api/authors", methods=["POST"])
def add_author():
    try:
        data = request.json
        name = data.get("name")
        description = data.get("description", "")

        if not name:
            return jsonify({"error": "Имя автора обязательно"}), 400

        # Проверяем, нет ли уже такого автора
        existing_author = Author.query.filter_by(name=name).first()
        if existing_author:
            return jsonify({"error": "Автор уже существует"}), 400

        new_author = Author(name=name, description=description)
        db.session.add(new_author)
        db.session.commit()

        return jsonify({
            "message": "Автор добавлен!",
            "id": new_author.id,
            "name": new_author.name
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/authors', methods=['GET'])
def search_authors():
    search_term = request.args.get('search', '')
    authors = Author.query.filter(Author.name.ilike(f"%{search_term}%")).limit(10).all()
    return jsonify([
        {"id": a.id, "name": a.name, "description": a.description} for a in authors
    ])


@app.route("/api/authors/<int:author_id>", methods=["PUT"])
def update_author(author_id):
    try:
        data = request.json
        name = data.get("name")
        description = data.get("description", "")

        if not name:
            return jsonify({"error": "Имя автора обязательно"}), 400

        author = Author.query.get(author_id)
        if not author:
            return jsonify({"error": "Автор не найден"}), 404

        # Проверяем, нет ли другого автора с таким именем
        existing_author = Author.query.filter(Author.name == name, Author.id != author_id).first()
        if existing_author:
            return jsonify({"error": "Автор с таким именем уже существует"}), 400

        author.name = name
        author.description = description
        db.session.commit()

        return jsonify({"message": "Автор обновлен!", "id": author.id, "name": author.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    try:
        author = Author.query.get(author_id)
        if not author:
            return jsonify({"error": "Автор не найден"}), 404

        db.session.delete(author)
        db.session.commit()

        return jsonify({"message": "Автор удален!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Получение всех жанров
@app.route("/api/genres", methods=["GET"])
def get_genres():
    try:
        genres = Genre.query.all()
        return jsonify([
            {"id": g.id, "name": g.name} 
            for g in genres
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Создание нового жанра
@app.route("/api/genres", methods=["POST"])
def create_genre():
    try:
        data = request.get_json()
        name = data.get("name")

        if not name:
            return jsonify({"error": "Название жанра обязательно"}), 400

        # Проверка на существование жанра с таким именем
        existing_genre = Genre.query.filter_by(name=name).first()
        if existing_genre:
            return jsonify({"error": "Жанр уже существует"}), 400

        new_genre = Genre(name=name)
        db.session.add(new_genre)
        db.session.commit()

        return jsonify({"id": new_genre.id, "name": new_genre.name}), 201
    except Exception as e:
        return jsonify({"error": f"Ошибка при создании жанра: {str(e)}"}), 500

# Поиск жанра по имени
@app.route("/api/genres/search", methods=["GET"])
def search_genre():
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({"error": "Параметр 'name' обязателен"}), 400

        genre = Genre.query.filter(Genre.name.ilike(f"%{name}%")).all()
        return jsonify([
            {"id": g.id, "name": g.name} 
            for g in genre
        ]), 200
    except Exception as e:
        return jsonify({"error": f"Ошибка при поиске жанра: {str(e)}"}), 500

# Обновление жанра
@app.route("/api/genres/<int:genre_id>", methods=["PUT"])
def update_genre(genre_id):
    try:
        data = request.get_json()
        name = data.get("name")

        if not name:
            return jsonify({"error": "Название жанра обязательно"}), 400

        genre = Genre.query.get(genre_id)
        if not genre:
            return jsonify({"error": "Жанр не найден"}), 404

        genre.name = name
        db.session.commit()

        return jsonify({"id": genre.id, "name": genre.name}), 200
    except Exception as e:
        return jsonify({"error": f"Ошибка при обновлении жанра: {str(e)}"}), 500

# Удаление жанра
@app.route("/api/genres/<int:genre_id>", methods=["DELETE"])
def delete_genre(genre_id):
    try:
        genre = Genre.query.get(genre_id)
        if not genre:
            return jsonify({"error": "Жанр не найден"}), 404

        db.session.delete(genre)
        db.session.commit()

        return jsonify({"message": "Жанр удален"}), 200
    except Exception as e:
        return jsonify({"error": f"Ошибка при удалении жанра: {str(e)}"}), 500
from flask import request, jsonify, session
from models import Book, User, SafeShelf, Role, UserInventory, BookGenre, Genre
from werkzeug.security import check_password_hash, generate_password_hash
from config import SECRET_KEY  # Используем SECRET_KEY для сессий
import datetime
import logging
import json
from app import app, db  # Убедитесь, что db и app импортированы

# Настройка сессий
app.secret_key = SECRET_KEY  # Установите SECRET_KEY в config.py

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from flask import request, jsonify, session
from models import User
from werkzeug.security import check_password_hash
import logging
import os
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route("/api/login", methods=["POST"])
def login_user():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email и пароль обязательны"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Неверный email или пароль"}), 401

        # Генерируем JWT токен
        token = jwt.encode(
            {'user_id': user.id, 'role_id': user.role_id},
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )

        return jsonify({
            "message": "Успешный вход",
            "token": token,  # Возвращаем токен
            "user": {
                "id": user.id,
                "role_id": user.role_id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "phone": user.phone,
                "birth_date": user.birth_date.isoformat() if user.birth_date else None
            }
        }), 200
    except Exception as e:
        logger.error(f"Ошибка при входе: {str(e)}")
        return jsonify({"error": f"Ошибка при входе: {str(e)}"}), 500
    
# Выход пользователя
@app.route("/api/logout", methods=["POST"])
def logout_user():
    try:
        session.pop("user_id", None)
        session.pop("role_id", None)
        return jsonify({"message": "Успешный выход"}), 200
    except Exception as e:
        logger.error(f"Ошибка при выходе: {str(e)}")
        return jsonify({"error": f"Ошибка при выходе: {str(e)}"}), 500
    
# Получение доступных книг с информацией о ячейках для карты/поиска (публичный эндпоинт)
@app.route('/api/books/available', methods=['GET'])
def get_available_books():
    try:
        # Логируем запрос для диагностики
        logger.debug("Запрос к /api/books/available начат")

        # Получаем книги со статусом "available"
        books = Book.query.filter_by(status="available").all()
        logger.debug(f"Найдено книг со статусом 'available': {len(books)}")

        result = []
        for book in books:
            # Логируем каждую книгу для диагностики
            logger.debug(f"Обработка книги: ID={book.id}, Title={book.title}, Status={book.status}")
            
            shelf = SafeShelf.query.get(book.safe_shelf_id) if book.safe_shelf_id else None
            result.append({
                **book.to_json(),
                "shelf_location": {
                    "id": shelf.id if shelf else None,
                    "name": shelf.name if shelf else "Не указано",
                    "address": shelf.address if shelf else "Не указано",
                    "latitude": shelf.latitude if shelf else None,
                    "longitude": shelf.longitude if shelf else None
                } if shelf else None
            })
        
        logger.debug(f"Возвращено {len(result)} доступных книг")
        return jsonify(result), 200
    except AttributeError as e:
        logger.error(f"Ошибка атрибута при получении доступных книг: {str(e)}")
        return jsonify({"error": f"Ошибка при получении доступных книг: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении доступных книг: {str(e)}")
        return jsonify({"error": f"Ошибка при получении доступных книг: {str(e)}"}), 500

# Получение всех книг (для отладки или поиска) — публичный эндпоинт
@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        # Получаем параметры из запроса
        title = request.args.get("search", "")  # Поиск по названию (title)
        author_id = request.args.get("author_id", type=int, default=None)  # По автору (позволяем None)
        safe_shelf_id = request.args.get("safe_shelf_id", type=int, default=None)  # По безопасной ячейке
        genre_id = request.args.get("genre_id", type=int, default=None)  # По жанру
        status = request.args.get("status", type=str, default=None)  # По статусу (available, reserved, in_hand)

        # Базовый запрос
        query = Book.query.join(BookGenre).filter(BookGenre.book_id == Book.id)

        # Применяем фильтры, если они указаны и не None
        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))  # Поиск по названию (нечувствительный к регистру)
        if author_id is not None:
            query = query.filter(Book.author_id == author_id)
        if safe_shelf_id is not None:
            query = query.filter(Book.safe_shelf_id == safe_shelf_id)
        if genre_id is not None:
            query = query.filter(BookGenre.genre_id == genre_id)
        if status:
            query = query.filter(Book.status == status)

        # Получаем книги
        books = query.all()

        logger.debug(f"Параметры запроса: {request.args}, возвращено {len(books)} книг")
        return jsonify([
            {
                "id": book.id,
                "title": book.title,
                "author_id": book.author_id,
                "description": book.description,
                "safe_shelf_id": book.safe_shelf_id,
                "user_id": book.user_id,
                "isbn": book.isbn,
                "status": book.status,
                "genres": [g.genre_id for g in book.genres],  # список жанров книги
                "path": book.path  # путь книги
            }
            for book in books
        ]), 200
    except Exception as e:
        logger.error(f"Ошибка при получении книг: {str(e)}")
        return jsonify({"error": f"Ошибка при получении книг: {str(e)}"}), 500


from flask import request, jsonify, session
from app import app, db
from models import Book, Genre, BookGenre
from datetime import datetime  # Правильный импорт

@app.route('/api/books', methods=['POST'])
def add_book():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json

    # Проверяем, переданы ли все нужные данные (исключаем isbn из обязательных, так как можем сгенерировать)
    required_fields = ["title", "author_id", "description", "user_id", "genre_ids"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Получаем данные из запроса
    title = data["title"]
    author_id = data["author_id"]
    description = data["description"]
    safe_shelf_id = data.get("safe_shelf_id")  # Может быть None
    user_id = data["user_id"]
    genre_ids = data["genre_ids"]
    status = data.get("status", "available")  # По умолчанию "available"

    # Если ISBN передан, используем его, иначе генерируем
    isbn = data.get("isbn")
    if not isbn:
        # Генерация ISBN-13
        def generate_isbn():
            # Префикс ISBN-13: 978 или 979
            prefix = random.choice(["978", "979"])
            # Код региона: 0 (пример, можно изменить)
            region = "0"
            # Код издателя: случайное 5-значное число
            publisher = str(random.randint(0, 99999)).zfill(5)
            # Номер книги: случайное 3-значное число
            book_number = str(random.randint(0, 999)).zfill(3)
            # Собираем первые 12 цифр
            isbn_base = prefix + region + publisher + book_number
            # Вычисляем контрольную цифру
            checksum = 0
            for i in range(12):
                digit = int(isbn_base[i])
                checksum += digit if i % 2 == 0 else digit * 3
            checksum = (10 - (checksum % 10)) % 10
            # Полный ISBN-13
            generated_isbn = isbn_base + str(checksum)
            
            # Проверяем уникальность ISBN в базе данных
            while Book.query.filter_by(isbn=generated_isbn).first():
                # Если ISBN уже существует, генерируем новый
                return generate_isbn()
            
            return generated_isbn

        isbn = generate_isbn()

    # Проверяем, что user_id соответствует сессии
    if user_id != session.get("user_id"):
        return jsonify({"error": "Недостаточно прав"}), 403

    # Проверяем, существуют ли переданные жанры
    existing_genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
    if len(existing_genres) != len(genre_ids):
        return jsonify({"error": "One or more genres do not exist"}), 400

    # Создаем книгу
    new_book = Book(
        title=title,
        author_id=author_id,
        description=description,
        safe_shelf_id=safe_shelf_id,
        user_id=user_id if status == "in_hand" else None,  # Связываем с пользователем, если в руках
        isbn=isbn,
        status=status
    )
    db.session.add(new_book)
    db.session.commit()

    # Добавляем жанры в BookGenre
    for genre_id in genre_ids:
        book_genre = BookGenre(book_id=new_book.id, genre_id=genre_id)
        db.session.add(book_genre)

    # Формируем новый путь книги
    path = []
    if status == "available" and safe_shelf_id:
        path.append({
            "user_id": None,  # Нет конкретного пользователя, книга на полке
            "timestamp": datetime.now().isoformat(),
            "action": "added",
            "location": "safe_shelf",
            "shelf_id": safe_shelf_id
        })
    elif status == "in_hand":
        path.append({
            "user_id": user_id,  # Пользователь, взявший книгу
            "timestamp": datetime.now().isoformat(),
            "action": "taken",
            "location": "у пользователя"
        })

    # Сохраняем путь как JSON
    new_book.path = json.dumps(path) if path else json.dumps([])

    db.session.commit()

    return jsonify({"message": "Book added successfully", "book_id": new_book.id, "isbn": isbn}), 201
# Добавление книги в инвентарь — защищённый эндпоинт
from datetime import datetime
import json

@app.route('/api/inventory', methods=['POST'])
def add_to_inventory():
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json
    user_id = data.get("user_id")
    book_id = data.get("book_id")

    if not user_id or not book_id:
        return jsonify({"error": "Требуются user_id и book_id"}), 400

    # Преобразуем user_id и book_id в int
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Некорректный формат user_id"}), 400

    try:
        book_id = int(book_id)
    except ValueError:
        return jsonify({"error": "Некорректный формат book_id"}), 400

    if user_id != session.get("user_id"):
        return jsonify({"error": "Недостаточно прав"}), 403

    # Проверяем, существует ли пользователь и книга
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user or not book:
        return jsonify({"error": "Пользователь или книга не найдены"}), 404

    # Проверяем, не находится ли книга уже в инвентаре
    existing_entry = UserInventory.query.filter_by(
        user_id=user_id,
        book_id=book_id
    ).first()
    if existing_entry:
        return jsonify({"error": "Книга уже в инвентаре пользователя"}), 400

    # Проверяем текущий статус книги
    if book.status != "available":
        return jsonify({"error": "Книга недоступна для добавления в инвентарь"}), 400

    # Обновляем путь книги
    current_path = book.path if isinstance(book.path, list) else json.loads(book.path) if book.path and isinstance(book.path, str) else []
    try:
        if book.status == "available" and book.safe_shelf_id:
            current_path.append({
                "user_id": None,
                "timestamp": datetime.now().isoformat(),
                "action": "added",
                "location": "safe_shelf",
                "shelf_id": book.safe_shelf_id
            })
        elif book.status == "in_hand":
            current_path.append({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "action": "taken",
                "location": "у пользователя"
            })
    except Exception as e:
        logger.error(f"Ошибка при обновлении пути: {str(e)}")
        return jsonify({"error": "Ошибка при обновлении пути книги"}), 500

    # Создаём новую запись в ИнвентарьПользователей
    try:
        inventory_entry = UserInventory(
            user_id=user_id,
            book_id=book_id
        )
        db.session.add(inventory_entry)

        # Обновляем книгу
        book.user_id = user_id
        book.status = "in_hand"
        book.path = json.dumps(current_path)  # Сериализуем список в JSON-строку
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении в инвентарь: {str(e)}")
        return jsonify({"error": "Ошибка при добавлении в инвентарь"}), 500

    return jsonify({"message": "Книга добавлена в инвентарь", "book_id": book_id}), 201
# Удаление книги из инвентаря — защищённый эндпоинт
@app.route('/api/inventory', methods=['DELETE'])
def remove_from_inventory():
    if not session.get("user_id") or session.get("role_id") != 2:
        return jsonify({"error": "Требуется авторизация как обычный пользователь"}), 401

    user = User.query.get(session.get("user_id"))
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    data = request.json
    book_id = data.get('book_id')
    if not book_id:
        return jsonify({"error": "Укажите ID книги"}), 400

    inventory_entry = UserInventory.query.filter_by(user_id=session.get("user_id"), book_id=book_id).first()
    if not inventory_entry:
        return jsonify({"error": "Книга не найдена в вашем инвентаре"}), 404

    db.session.delete(inventory_entry)
    db.session.commit()

    return jsonify({"message": "Книга удалена из инвентаря"}), 200

# Получение инвентаря пользователя — защищённый эндпоинт
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    if not session.get("user_id") or session.get("role_id") != 2:
        return jsonify({"error": "Требуется авторизация как обычный пользователь"}), 401

    user = User.query.get(session.get("user_id"))
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    inventory = UserInventory.query.filter_by(user_id=session.get("user_id")).all()
    return jsonify([entry.to_json() for entry in inventory]), 200

# Поиск книги по ISBN — публичный эндпоинт
@app.route('/api/books/isbn/<string:isbn>', methods=['GET'])
def get_book_by_isbn(isbn):
    try:
        book = Book.query.filter_by(isbn=isbn).first()
        if not book:
            return jsonify({"error": "Книга не найдена"}), 404

        shelf = SafeShelf.query.get(book.safe_shelf_id) if book.safe_shelf_id else None
        path = json.loads(book.path) if book.path else []
        is_in_inventory = UserInventory.query.filter_by(user_id=session.get("user_id"), book_id=book.id).first() if session.get("user_id") else None

        result = {
            **book.to_json(),
            "current_location": {
                "shelf_name": shelf.name if shelf else "Не указано",
                "address": shelf.address if shelf else "Не указано",
                "latitude": shelf.latitude if shelf else None,
                "longitude": shelf.longitude if shelf else None,
                "status": book.status,
                "user_name": User.query.get(book.user_id).name if book.user_id and book.status == "in_hand" else None
            } if shelf else {
                "shelf_name": "У пользователя" if book.status == "in_hand" else "Не указано",
                "address": "Не указано",
                "latitude": None,
                "longitude": None,
                "status": book.status,
                "user_name": User.query.get(book.user_id).name if book.user_id and book.status == "in_hand" else None
            },
            "path_history": path,
            "is_in_inventory": bool(is_in_inventory)
        }
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Ошибка при поиске книги по ISBN: {str(e)}")
        return jsonify({"error": f"Ошибка при поиске книги: {str(e)}"}), 500

# Обновление статистики — публичный эндпоинт
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        # Общее количество пользователей
        registered_users = User.query.count()
        logger.debug(f"Количество пользователей: {registered_users}")

        # Общее количество безопасных ячеек
        total_safeshelves = SafeShelf.query.count()
        logger.debug(f"Количество безопасных ячеек: {total_safeshelves}")

        # Общее количество доступных книг (со статусом "available")
        available_books = Book.query.filter_by(status="available").count()
        logger.debug(f"Количество доступных книг: {available_books}")

        # Общее количество зарезервированных книг (со статусом "reserved")
        reserved_books = Book.query.filter_by(status="reserved").count()
        logger.debug(f"Количество зарезервированных книг: {reserved_books}")

        # Общее количество книг "в руках" (со статусом "in_hand")
        in_hand_books = Book.query.filter_by(status="in_hand").count()
        logger.debug(f"Количество книг в руках: {in_hand_books}")

        # Общее количество книг в системе
        total_books = Book.query.count()
        logger.debug(f"Общее количество книг: {total_books}")

        stats = {
            "registeredUsers": registered_users,
            "totalSafeshelves": total_safeshelves,
            "availableBooks": available_books,
            "reservedBooks": reserved_books,
            "inHandBooks": in_hand_books,
            "totalBooks": total_books
        }

        logger.debug(f"Статистика: {stats}")
        return jsonify(stats), 200
    except AttributeError as e:
        logger.error(f"Ошибка атрибута: {str(e)}")
        return jsonify({"error": "Ошибка доступа к модели или данным. Проверьте базу данных и модели."}), 500
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {str(e)}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500
    


from flask import request, jsonify, session
from app import app, db
from models import UserInventory, Book

@app.route('/api/inventory/<int:user_id>', methods=['GET'])
def get_user_inventory(user_id):
    if not session.get("user_id") or session.get("user_id") != user_id:
        return jsonify({"error": "Требуется авторизация или доступ запрещён"}), 401

    inventory_entries = UserInventory.query.filter_by(user_id=user_id).all()
    inventory_data = [
        {
            "user_id": entry.user_id,
            "book_id": entry.book_id,
            "book": entry.book.to_json() if entry.book else None,
            "added_at": entry.added_at.isoformat()
        }
        for entry in inventory_entries
    ]
    return jsonify(inventory_data), 200

@app.route('/api/books/compatible', methods=['GET'])
def get_compatible_books():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Требуется авторизация"}), 401
    
    user = User.query.get_or_404(user_id)
    books = Book.query.all()
    
    compatible_books = []
    for book in books:
        score = calculate_compatibility(book, user)
        compatible_books.append({
            "id": book.id,
            "title": book.title,
            "author_id": book.author_id,
            "status": book.status,
            "safe_shelf_id": book.safe_shelf_id,
            "compatibility": score
        })
    
    return jsonify(compatible_books), 200

def calculate_compatibility(book, user):
    score = 0
    genre_weight = 0.4
    author_weight = 0.3
    status_weight = 0.3
    
    # Совместимость по жанрам
    matching_genres = len(set(book.genre_ids) & set([g.id for g in user.preferences.genres])) if user.preferences.genres else 0
    score += genre_weight * (matching_genres / len(book.genre_ids) if book.genre_ids else 0)
    
    # Совместимость по авторам
    score += author_weight * (book.author_id in [a.id for a in user.preferences.authors] if user.preferences.authors else 0)
    
    # Совместимость по статусу
    score += status_weight * (book.status == "available")
    
    return round(score, 2)



@app.route('/api/books/<int:book_id>/release', methods=['PUT'])
def release_book(book_id):
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json
    user_id = data.get("user_id")
    safe_shelf_id = data.get("safe_shelf_id")

    if not user_id or not safe_shelf_id:
        return jsonify({"error": "Требуются user_id и safe_shelf_id"}), 400

    if user_id != session.get("user_id"):
        return jsonify({"error": "Недостаточно прав"}), 403

    try:
        # Получаем книгу
        book = Book.query.get_or_404(book_id)
        if book.user_id != user_id or book.status != "in_hand":
            return jsonify({"error": "Книга не принадлежит вам или недоступна для отпуска"}), 400

        # Проверяем, существует ли указанная ячейка
        shelf = SafeShelf.query.get(safe_shelf_id)
        if not shelf:
            return jsonify({"error": "Указанная ячейка не существует"}), 400

        # Обновляем книгу
        book.user_id = None  # Теперь это допустимо, так как nullable=True
        book.status = "available"
        book.safe_shelf_id = safe_shelf_id

        # Обновляем путь книги
        path = json.loads(book.path) if book.path else []
        path.append({
            "user_id": None,
            "timestamp": datetime.now().isoformat(),
            "action": "returned",
            "location": "safe_shelf",
            "shelf_id": safe_shelf_id
        })
        book.path = json.dumps(path)

        # Удаляем запись из UserInventory, если существует
        user_inventory = UserInventory.query.filter_by(user_id=user_id, book_id=book_id).first()
        if user_inventory:
            db.session.delete(user_inventory)

        db.session.commit()
        logger.debug(f"Книга {book_id} успешно отпущена в ячейку {safe_shelf_id}")
        return jsonify({
            "message": "Книга отпущена в ячейку",
            "book_id": book.id,
            "book": book.to_json()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при отпускании книги {book_id}: {str(e)}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500
    
@app.route('/api/books/<int:book_id>/take', methods=['PUT'])
def take_book(book_id):
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    data = request.json
    user_id = data.get("user_id")
    book_code = data.get("book_code")

    if user_id != session.get("user_id"):
        return jsonify({"error": "Недостаточно прав"}), 403

    book = Book.query.get_or_404(book_id)
    if book.status != "available":
        return jsonify({"error": "Книга недоступна для взятия"}), 400

    # Проверка кода книги (например, ISBN)
    if book.isbn != book_code:
        return jsonify({"error": "Неверный код книги"}), 400

    book.user_id = user_id
    book.status = "in_hand"
    book.safe_shelf_id = None

    # Обновляем путь книги
    path = json.loads(book.path) if book.path else []
    path.append({
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "action": "taken",
        "location": "у пользователя"
    })
    book.path = json.dumps(path)

    db.session.commit()
    return jsonify({"message": "Книга успешно взята", "book_id": book.id}), 200


from flask import jsonify, request
from app import app, db
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASSWORD
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_html_table(book_list):
    table = """
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <thead>
            <tr>
                <th>Название</th>
                <th>Автор</th>
                <th>ISBN</th>
                <th>Жанры</th>
                <th>Место хранения</th>
            </tr>
        </thead>
        <tbody>
    """
    for book in book_list:
        table += f"""
            <tr>
                <td>{book.get('title', 'Без названия')}</td>
                <td>{book.get('author', 'Неизвестный автор')}</td>
                <td>{book.get('isbn', 'Не указан')}</td>
                <td>{book.get('genres', 'Не указаны')}</td>
                <td>{book.get('shelf', 'Не указано')}</td>
            </tr>
        """
    table += """
        </tbody>
    </table>
    """
    return table

@app.route('/api/send-email', methods=['POST'])
def send_email():
    try:
        data = request.get_json()
        recipient_email = data.get('email')
        message = data.get('message')
        book_list = data.get('books', [])

        if not recipient_email or not message:
            return jsonify({"error": "Email и сообщение обязательны"}), 400

        # Настройки SMTP
        sender_email = EMAIL_USER
        password = EMAIL_PASSWORD

        # Создание письма
        msg = MIMEMultipart()
        msg['Subject'] = 'Обратная связь с сайта'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Генерируем HTML-таблицу из списка книг
        html_table = generate_html_table(book_list)

        # Формируем тело письма: сообщение + таблица
        html_body = f"""
        <html>
            <body>
                <p>{message}</p>
                <h3>Список доступных книг:</h3>
                {html_table}
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Подключение к SMTP-серверу Gmail
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.send_message(msg)
                logger.debug(f"Письмо успешно отправлено на {recipient_email}")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Ошибка аутентификации SMTP: {str(e)}")
            return jsonify({"error": "Ошибка аутентификации. Проверьте email и пароль приложения."}), 401
        except smtplib.SMTPException as e:
            logger.error(f"Ошибка SMTP: {str(e)}")
            return jsonify({"error": f"Ошибка при отправке письма: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Неизвестная ошибка SMTP: {str(e)}")
            return jsonify({"error": f"Неизвестная ошибка при отправке письма: {str(e)}"}), 500

        return jsonify({
            "message": "Письмо с таблицей успешно отправлено",
            "recipient": recipient_email
        }), 200
    except Exception as e:
        logger.error(f"Общая ошибка при обработке запроса: {str(e)}")
        return jsonify({"error": f"Ошибка при обработке запроса: {str(e)}"}), 500