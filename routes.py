from app import app, db
from flask import request, jsonify, g
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from models import Topic, Message,BookRequest , Role, User, SafeShelf, Author, Book, BookGenre, Genre, Review, UserInventory
import os
import jwt
from config import SECRET_KEY, ALGORITHM
from datetime import datetime  # Правильный импорт
import random
from sqlalchemy.exc import SQLAlchemyError
import requests
import random
import json
import datetime
from flask import jsonify, request, session
from app import app, db
from models import Book, Genre, BookGenre, Notification,Favorite, Notification, SafeShelf, Conversation, ChatMessage
import logging

import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASSWORD  # Добавьте эти переменные в config.py
import json

import datetime
import logging

from flask import send_from_directory
from werkzeug.utils import secure_filename

# Эндпоинт для добавления отзыва
@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        if not request.is_json:
            return jsonify({'error': 'Ожидается JSON в теле запроса'}), 400

        data = request.get_json()
        book_id = data.get('book_id')
        user_id = data.get('user_id')
        name = data.get('name')
        text = data.get('text')
        rating = data.get('rating')

        if not all([book_id, user_id, name, text, rating]):
            return jsonify({'error': 'Требуются book_id, user_id, name, text и rating'}), 400

        book_id = int(book_id)
        user_id = int(user_id)
        rating = int(rating)

        if rating < 1 or rating > 5:
            return jsonify({'error': 'Рейтинг должен быть от 1 до 5'}), 400

        # Проверяем, существует ли уже отзыв от этого пользователя для этой книги
        existing_review = Review.query.filter_by(book_id=book_id, user_id=user_id).first()
        if existing_review:
            return jsonify({'error': 'Вы уже оставили отзыв для этой книги'}), 400

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        review = Review(
            book_id=book_id,
            user_id=user_id,
            name=name,
            text=text,
            rating=rating
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({
            'message': 'Отзыв успешно добавлен',
            'review': {
                'book_id': review.book_id,
                'user_id': review.user_id,
                'name': review.name,
                'text': review.text,
                'rating': review.rating
            }
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при добавлении отзыва: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для получения отзывов по книге
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        book_id = request.args.get('book_id', type=int)
        if not book_id:
            return jsonify({'error': 'Требуется book_id'}), 400

        reviews = Review.query.filter_by(book_id=book_id).all()
        return jsonify([{
            'book_id': review.book_id,
            'user_id': review.user_id,
            'name': review.name,
            'text': review.text,
            'rating': review.rating
        } for review in reviews]), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении отзывов: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинты для избранного
@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'error': 'Требуется user_id'}), 400

        favorites = Favorite.query.filter_by(user_id=user_id).all()
        return jsonify([{'user_id': fav.user_id, 'book_id': fav.book_id} for fav in favorites]), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении избранного: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    try:
        if not request.is_json:
            return jsonify({'error': 'Ожидается JSON в теле запроса'}), 400

        data = request.get_json()
        user_id = data.get('user_id')
        book_id = data.get('book_id')

        if not all([user_id, book_id]):
            return jsonify({'error': 'Требуются user_id и book_id'}), 400

        user_id = int(user_id)
        book_id = int(book_id)

        if Favorite.query.filter_by(user_id=user_id, book_id=book_id).first():
            return jsonify({'error': 'Книга уже в избранном'}), 400

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        favorite = Favorite(user_id=user_id, book_id=book_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'message': 'Книга добавлена в избранное'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при добавлении в избранное: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/favorites/<int:user_id>/<int:book_id>', methods=['DELETE'])
def remove_favorite(user_id, book_id):
    try:
        favorite = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
        if not favorite:
            return jsonify({'error': 'Книга не найдена в избранном'}), 404

        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'message': 'Книга удалена из избранного'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при удалении из избранного: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для получения книги по ID
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404

        return jsonify({
            "id": book.id,
            "title": book.title,
            "author_id": book.author_id,
            "description": book.description,
            "safe_shelf_id": book.safe_shelf_id,
            "user_id": book.user_id,
            "isbn": book.isbn,
            "status": book.status,
            "genres": [g.genre_id for g in book.genres],
            "path": book.path
        }), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении книги: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для обновления книги и создания уведомлений
@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    try:
        if not request.is_json:
            return jsonify({'error': 'Ожидается JSON в теле запроса'}), 400

        data = request.get_json()
        status = data.get('status')
        safe_shelf_id = data.get('safe_shelf_id', type=int)

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404

        if status:
            book.status = status
        if safe_shelf_id is not None:
            book.safe_shelf_id = safe_shelf_id

        db.session.commit()

        # Создаем уведомления, если книга помещена в безопасную ячейку
        if status == 'in_safe_shelf' and safe_shelf_id:
            safe_shelf = SafeShelf.query.get(safe_shelf_id)
            if not safe_shelf:
                return jsonify({'error': 'Безопасная ячейка не найдена'}), 404

            favorites = Favorite.query.filter_by(book_id=book_id).all()
            for favorite in favorites:
                notification = Notification(
                    user_id=favorite.user_id,
                    book_id=book_id,
                    safe_shelf_id=safe_shelf_id,
                    message=f"Книга '{book.title}' теперь доступна в безопасной ячейке по адресу: {safe_shelf.address}"
                )
                db.session.add(notification)
            db.session.commit()

        return jsonify({
            "id": book.id,
            "title": book.title,
            "author_id": book.author_id,
            "description": book.description,
            "safe_shelf_id": book.safe_shelf_id,
            "user_id": book.user_id,
            "isbn": book.isbn,
            "status": book.status,
            "genres": [g.genre_id for g in book.genres],
            "path": book.path
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при обновлении книги: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для получения уведомлений
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'error': 'Требуется user_id'}), 400

        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
        return jsonify([{
            'id': notif.id,
            'user_id': notif.user_id,
            'book_id': notif.book_id,
            'safe_shelf_id': notif.safe_shelf_id,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat() if notif.created_at else None
        } for notif in notifications]), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении уведомлений: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для отправки запроса на книгу (создает беседу)
@app.route('/api/book_requests', methods=['POST'])
def create_book_request():
    try:
        if not request.is_json:
            return jsonify({'error': 'Ожидается JSON в теле запроса'}), 400

        data = request.get_json()
        book_id = data.get('book_id')
        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        content = data.get('content')

        if not all([book_id, sender_id, recipient_id, content]):
            return jsonify({'error': 'Требуются book_id, sender_id, recipient_id и content'}), 400

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Книга не найдена'}), 404

        sender = User.query.get(sender_id)
        if not sender:
            return jsonify({'error': 'Отправитель не найден'}), 404

        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({'error': 'Получатель не найден'}), 404

        # Проверяем, существует ли уже беседа между этими пользователями по этой книге
        existing_conversation = Conversation.query.filter_by(
            sender_id=sender_id,
            recipient_id=recipient_id,
            book_id=book_id
        ).first()

        if existing_conversation:
            # Если беседа существует, добавляем сообщение в неё
            message = ChatMessage(
                conversation_id=existing_conversation.id,
                sender_id=sender_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            return jsonify({
                'message': 'Сообщение добавлено в существующую беседу',
                'conversation_id': existing_conversation.id
            }), 200

        # Создаем новую беседу
        conversation = Conversation(
            sender_id=sender_id,
            recipient_id=recipient_id,
            book_id=book_id
        )
        db.session.add(conversation)
        db.session.flush()  # Получаем ID беседы перед коммитом

        # Создаем первое сообщение в беседе
        message = ChatMessage(
            conversation_id=conversation.id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({
            'message': 'Запрос на книгу отправлен, беседа создана',
            'conversation_id': conversation.id
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при создании запроса: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для получения списка бесед пользователя
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'error': 'Требуется user_id'}), 400

        # Получаем беседы, где пользователь является отправителем или получателем
        conversations = Conversation.query.filter(
            (Conversation.sender_id == user_id) | (Conversation.recipient_id == user_id)
        ).order_by(Conversation.created_at.desc()).all()

        return jsonify([conv.to_json() for conv in conversations]), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении бесед: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для получения сообщений в беседе
@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    try:
        messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.created_at.asc()).all()
        return jsonify([msg.to_json() for msg in messages]), 200
    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении сообщений: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

# Эндпоинт для отправки сообщения в беседе
@app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
def send_message(conversation_id):
    try:
        if not request.is_json:
            return jsonify({'error': 'Ожидается JSON в теле запроса'}), 400

        data = request.get_json()
        sender_id = data.get('sender_id')
        content = data.get('content')

        if not all([sender_id, content]):
            return jsonify({'error': 'Требуются sender_id и content'}), 400

        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Беседа не найдена'}), 404

        # Проверяем, что отправитель является участником беседы
        if conversation.sender_id != sender_id and conversation.recipient_id != sender_id:
            return jsonify({'error': 'У вас нет доступа к этой беседе'}), 403

        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()

        return jsonify(message.to_json()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Ошибка при отправке сообщения: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
    
# Папка для хранения аватаров
UPLOAD_FOLDER = 'uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        if not users:
            return jsonify({'message': 'Пользователи не найдены'}), 200

        return jsonify([{
            'user_id': user.id,
            'name': user.name,
            'email': user.email
        } for user in users]), 200

    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении пользователей: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


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

# Удаление темы и всех её сообщений
@app.route('/api/topic/<int:id>', methods=['DELETE'])
def delete_topic(id):
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    user = User.query.get(session["user_id"])
    if not user or user.role.name != "admin":
        return jsonify({"error": "Недостаточно прав"}), 403

    try:
        topic = Topic.query.get_or_404(id)
        Message.query.filter_by(topic_id=id).delete()
        db.session.delete(topic)
        db.session.commit()
        return jsonify({"message": "Тема удалена"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении темы {id}: {str(e)}")
        return jsonify({"error": f"Ошибка при удалении темы: {str(e)}"}), 500

# Удаление одного сообщения
@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    if not session.get("user_id"):
        return jsonify({"error": "Требуется авторизация"}), 401

    user = User.query.get(session["user_id"])
    if not user or user.role_id != 1:
        return jsonify({"error": "Недостаточно прав"}), 403

    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({"message": "Сообщение удалено"}), 200


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

        # Генерация токена
        token = jwt.encode(
            {'user_id': user.id, 'role_id': user.role_id},
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )

        # Обновляем поля из фронта (если пришли)
        user.name = data.get("name", user.name)
        user.avatar_url = data.get("avatar_url", user.avatar_url)
        user.bio = data.get("bio", user.bio)
        user.phone = data.get("phone", user.phone)
        birth_date = data.get("birth_date")
        if birth_date:
            user.birth_date = datetime.fromisoformat(birth_date)

        # Сохраняем обновлённого пользователя
        db.session.commit()

        return jsonify({
            "message": "Успешный вход",
            "token": token,
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

        # Базовый запрос без JOIN, чтобы не исключать книги без жанров
        query = Book.query

        # Применяем JOIN только если фильтр по жанру указан
        if genre_id is not None:
            query = query.join(BookGenre).filter(BookGenre.genre_id == genre_id)

        # Применяем фильтры, если они указаны и не None
        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))  # Поиск по названию (нечувствительный к регистру)
        if author_id is not None:
            query = query.filter(Book.author_id == author_id)
        if safe_shelf_id is not None:
            query = query.filter(Book.safe_shelf_id == safe_shelf_id)
        if status:
            query = query.filter(Book.status.ilike(status))  # Игнорируем регистр для статуса

        # Получаем книги
        books = query.all()

        # Логируем SQL-запрос для отладки
        logger.debug(f"Сгенерированный SQL: {query.statement}")
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

import requests
import random
import json
import datetime
from flask import jsonify, request, session
from app import app, db
from models import Book, Genre, BookGenre
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/books/fetch-isbn', methods=['POST'])
def fetch_isbn():
    data = request.json

    # Проверяем, передан ли заголовок книги
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400

    title = data['title']
    isbn = None

    # Пробуем найти ISBN через Google Books API
    try:
        GOOGLE_BOOKS_API_KEY = "AIzaSyB74WeOBbZUwdtLYsCmvWjdI2k9gMuG01o"
        api_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title.replace(' ', '+')}&key={GOOGLE_BOOKS_API_KEY}"
        response = requests.get(api_url)
        response.raise_for_status()
        result = response.json()

        if result.get('items'):
            book_data = result['items'][0]['volumeInfo']
            industry_identifiers = book_data.get('industryIdentifiers', [])
            for identifier in industry_identifiers:
                if identifier['type'] == 'ISBN_13':
                    isbn = identifier['identifier']
                    break
                elif identifier['type'] == 'ISBN_10':
                    isbn = identifier['identifier']
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ошибка при запросе к Google Books API: {str(e)}. Генерируем ISBN.")

    # Если ISBN не найден, генерируем его
    if not isbn:
        def generate_isbn():
            prefix = random.choice(["978", "979"])
            region = "0"
            publisher = str(random.randint(0, 99999)).zfill(5)
            book_number = str(random.randint(0, 999)).zfill(3)
            isbn_base = prefix + region + publisher + book_number
            checksum = 0
            for i in range(12):
                digit = int(isbn_base[i])
                checksum += digit if i % 2 == 0 else digit * 3
            checksum = (10 - (checksum % 10)) % 10
            generated_isbn = isbn_base + str(checksum)
            return generated_isbn if not Book.query.filter_by(isbn=generated_isbn).first() else generate_isbn()

        isbn = generate_isbn()

    return jsonify({"isbn": isbn}), 200

@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json

    # Проверяем, переданы ли все нужные данные
    required_fields = ["title", "author_id", "description", "user_id", "genre_ids", "isbn"]
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
    isbn = data["isbn"]

    # Проверяем, существует ли пользователь
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Проверяем, существуют ли переданные жанры
    existing_genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
    if len(existing_genres) != len(genre_ids):
        return jsonify({"error": "One or more genres do not exist"}), 400

    # Проверяем, существует ли книга с таким ISBN
    if Book.query.filter_by(isbn=isbn).first():
        return jsonify({"error": "Book with this ISBN already exists"}), 400

    try:
        # Создаем книгу
        new_book = Book(
            title=title,
            author_id=author_id,
            description=description,
            safe_shelf_id=safe_shelf_id,
            user_id=user_id if status == "in_hand" else None,
            isbn=isbn,
            status=status
        )
        db.session.add(new_book)
        db.session.flush()  # Получаем book.id

        # Добавляем жанры в BookGenre
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=new_book.id, genre_id=genre_id)
            db.session.add(book_genre)

        # Формируем путь книги
        path = []
        if status == "available" and safe_shelf_id:
            path.append({
                "user_id": None,
                "timestamp": datetime.now().isoformat(),
                "action": "added",
                "location": "safe_shelf",
                "shelf_id": safe_shelf_id
            })
        elif status == "in_hand":
            path.append({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "action": "taken",
                "location": "у пользователя"
            })

        new_book.path = json.dumps(path) if path else json.dumps([])


        # Добавляем книгу в инвентарь, если статус "in_hand"
        if status == "in_hand":
            inventory_entry = UserInventory(
                user_id=user_id,
                book_id=new_book.id
            )
            db.session.add(inventory_entry)

        db.session.commit()
        logger.info(f"Книга создана и добавлена в инвентарь: book_id={new_book.id}, user_id={user_id}")
        return jsonify({
            "message": "Book added successfully",
            "book_id": new_book.id,
            "isbn": isbn
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании книги: {str(e)}")
        return jsonify({"error": f"Не удалось создать книгу: {str(e)}"}), 500

from datetime import datetime
import json

@app.route('/api/inventory', methods=['POST'])
def add_to_inventory():
    data = request.json
    user_id = data.get("user_id")
    book_id = data.get("book_id")

    if not user_id or not book_id:
        return jsonify({"error": "Требуются user_id и book_id"}), 400

    # Преобразуем user_id и book_id в int
    try:
        user_id = int(user_id)
        book_id = int(book_id)
    except ValueError:
        return jsonify({"error": "Некорректный формат user_id или book_id"}), 400

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

    # Создаём новую запись в Инвентарь
    try:
        inventory_entry = UserInventory(
            user_id=user_id,
            book_id=book_id
        )
        db.session.add(inventory_entry)

        # Обновляем книгу
        book.user_id = user_id
        book.status = "in_hand"
        book.path = json.dumps(current_path)  # Сериализуем список
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





@app.route('/api/books/<int:book_id>/release', methods=['PUT'])
def release_book(book_id):
    try:
        # Получаем данные из тела запроса
        data = request.json
        user_id = data.get("user_id")
        safe_shelf_id = data.get("safe_shelf_id")
        new_status = data.get("status", "available")  # По умолчанию "available"

        # Получаем книгу
        book = Book.query.get_or_404(book_id)

        # Обновляем книгу данными из запроса
        book.user_id = None
        book.status = new_status
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



@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    logger.info(f"Сессия: {session}")
    if not session.get("user_id"):
        logger.error("Отсутствует user_id в сессии")
        return jsonify({"error": "Требуется авторизация"}), 401

    user_id = session.get("user_id")
    
    # Проверяем, существует ли пользователь
    user = User.query.get(user_id)
    if not user:
        logger.error(f"Пользователь с id={user_id} не найден")
        return jsonify({"error": "Пользователь не найден"}), 404

    # Проверяем, существует ли книга
    book = Book.query.get(id)
    if not book:
        logger.error(f"Книга с id={id} не найдена")
        return jsonify({"error": "Книга не найдена"}), 404

    try:
        # Удаляем связанные записи
        BookGenre.query.filter_by(book_id=book.id).delete()
        UserInventory.query.filter_by(book_id=book.id).delete()

        # Удаляем книгу
        db.session.delete(book)
        db.session.commit()
        logger.info(f"Книга удалена: book_id={id}, user_id={user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении книги: {str(e)}")
        return jsonify({"error": f"Не удалось удалить книгу: {str(e)}"}), 500

    return jsonify({"message": "Книга успешно удалена", "book_id": id}), 200

@app.route('/api/books/update/<int:id>', methods=['PUT'])
def edit_book(id):
    logger.info(f"Сессия: {session}")
    if not session.get("user_id"):
        logger.error("Отсутствует user_id в сессии")
        return jsonify({"error": "Требуется авторизация"}), 401

    # Проверяем, существует ли книга
    book = Book.query.get(id)
    if not book:
        logger.error(f"Книга с id={id} не найдена")
        return jsonify({"error": "Книга не найдена"}), 404

    data = request.json

    # Проверяем, переданы ли данные
    if not data:
        logger.error("Данные не переданы")
        return jsonify({"error": "Данные не переданы"}), 400

    # Получаем данные из запроса
    title = data.get("title", book.title)
    author_id = data.get("author_id", book.author_id)
    description = data.get("description", book.description)
    safe_shelf_id = data.get("safe_shelf_id", book.safe_shelf_id)
    user_id = data.get("user_id", session.get("user_id"))  # По умолчанию берем из сессии
    genre_ids = data.get("genre_ids", [bg.genre_id for bg in book.genres])
    status = data.get("status", book.status)
    isbn = data.get("isbn", book.isbn)

    logger.info(f"Полученные данные: {data}")

    # Проверяем, существует ли пользователь
    user = User.query.get(user_id)
    if not user:
        logger.error(f"Пользователь с id={user_id} не найден")
        return jsonify({"error": "Пользователь не найден"}), 404

    # Проверяем, является ли пользователь администратором
    is_admin = user.role_id == 1
    logger.info(f"Роль пользователя: {user.role_id}, администратор: {is_admin}")

    # Для неадминов проверяем соответствие user_id
    if not is_admin and str(session.get("user_id")) != str(user_id):
        logger.error(f"Несоответствие user_id: сессия={session.get('user_id')}, запрос={user_id}")
        return jsonify({"error": "Несоответствие идентификатора пользователя"}), 403

    # Администратор может редактировать любые книги, игнорируя некоторые проверки
    if not is_admin:
        # Для неадминов проверяем, не принадлежит ли книга другому пользователю
        if book.user_id and str(book.user_id) != str(user_id):
            logger.error(f"Книга принадлежит другому пользователю: book.user_id={book.user_id}, user_id={user_id}")
            return jsonify({"error": "Вы не можете редактировать книгу другого пользователя"}), 403

    # Проверяем, существует ли книга с таким ISBN (кроме текущей книги), но только для неадминов
    if not is_admin:
        existing_book = Book.query.filter(Book.isbn == isbn, Book.id != id).first()
        if existing_book:
            logger.error(f"Книга с ISBN={isbn} уже существует")
            return jsonify({"error": "Книга с таким ISBN уже существует"}), 400

    # Проверяем жанры только для неадминов
    if not is_admin:
        existing_genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
        if len(existing_genres) != len(genre_ids):
            logger.error(f"Некорректные жанры: genre_ids={genre_ids}")
            return jsonify({"error": "Один или несколько жанров не существуют"}), 400

    try:
        # Обновляем поля книги
        book.title = title
        book.author_id = author_id
        book.description = description
        book.safe_shelf_id = safe_shelf_id
        book.isbn = isbn
        book.status = status
        book.user_id = user_id if status == "in_hand" else None

        # Обновляем жанры: удаляем старые и добавляем новые
        BookGenre.query.filter_by(book_id=book.id).delete()
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=book.id, genre_id=genre_id)
            db.session.add(book_genre)

        # Обновляем путь книги
        path = json.loads(book.path) if book.path else []
        if status == "available" and safe_shelf_id and book.status != "available":
            path.append({
                "user_id": None,
                "timestamp": datetime.now().isoformat(),
                "action": "returned",
                "location": "safe_shelf",
                "shelf_id": safe_shelf_id
            })
        elif status == "in_hand" and book.status != "in_hand":
            path.append({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "action": "taken",
                "location": "у пользователя"
            })
        book.path = json.dumps(path)

        # Обновляем инвентарь
        UserInventory.query.filter_by(book_id=book.id).delete()
        if status == "in_hand":
            inventory_entry = UserInventory(user_id=user_id, book_id=book.id)
            db.session.add(inventory_entry)

        # Завершаем транзакцию
        db.session.commit()
        logger.info(f"Книга обновлена: book_id={book.id}, user_id={user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении книги: {str(e)}")
        return jsonify({"error": f"Не удалось обновить книгу: {str(e)}"}), 500

    return jsonify({"message": "Книга успешно обновлена", "book_id": book.id, "isbn": isbn}), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        return jsonify(user.to_json()), 200

    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при получении пользователя: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
    
    from werkzeug.security import generate_password_hash

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['name', 'email', 'role_id', 'password']):
            return jsonify({'error': 'Не указаны все обязательные поля'}), 400

        # Проверяем, существует ли email
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email уже зарегистрирован'}), 400

        # Проверяем, существует ли роль
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Указанная роль не найдена'}), 404

        # Создаём нового пользователя
        new_user = User(
            name=data['name'],
            email=data['email'],
            role_id=int(data['role_id']),
            password=generate_password_hash(data['password'], method='pbkdf2:sha256'),
            bio=data.get('bio'),
            phone=data.get('phone'),
            birth_date=datetime.datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None,
            avatar_url=data.get('avatar_url')
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify(new_user.to_json()), 201

    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except ValueError as e:
        logger.error(f'Ошибка формата данных: {str(e)}')
        return jsonify({'error': f'Неверный формат данных: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Ошибка при создании пользователя: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
    
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        if 'role_id' in data:
            role = Role.query.get(data['role_id'])
            if not role:
                return jsonify({'error': 'Указанная роль не найдена'}), 404
            user.role_id = int(data['role_id'])

        if 'bio' in data:
            user.bio = data['bio']
        if 'phone' in data:
            user.phone = data['phone']
        if 'birth_date' in data:
            user.birth_date = datetime.datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data['birth_date'] else None
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']

        db.session.commit()

        return jsonify(user.to_json()), 200

    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except ValueError as e:
        logger.error(f'Ошибка формата данных: {str(e)}')
        return jsonify({'error': f'Неверный формат данных: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Ошибка при обновлении пользователя: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
    

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'Пользователь удалён'}), 200

    except SQLAlchemyError as e:
        logger.error(f'Ошибка базы данных: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f'Ошибка при удалении пользователя: {str(e)}')
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
    
@app.route('/api/book/movements/<int:book_id>', methods=['GET'])
def get_book_movements(book_id):
    try:
        # Получаем книгу по ID
        book = Book.query.get(book_id)
        if not book:
            logger.error(f"Книга не найдена: book_id={book_id}")
            return jsonify({"error": "Книга не найдена"}), 404

        # Извлекаем и декодируем путь
        path_data = book.path
        if not path_data or (isinstance(path_data, str) and not path_data.strip()):
            logger.info(f"Путь книги пуст: book_id={book_id}")
            return jsonify({"message": "История передвижений отсутствует"}), 200

        # Преобразуем JSON-строку в список, если это строка
        if isinstance(path_data, str):
            import json
            path_data = json.loads(path_data)

        # Преобразуем данные пути в читаемый формат
        movements = []
        for movement in path_data:
            user_id = movement.get("user_id")
            user_name = User.query.get(user_id).name if user_id else "Не указан"
            timestamp = movement.get("timestamp")
            action = movement.get("action")
            location = movement.get("location")
            shelf_id = movement.get("shelf_id")

            # Форматируем дату и время
            from datetime import datetime
            date_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_date = date_time.strftime("%d.%m.%Y")
            formatted_time = date_time.strftime("%H:%M:%S")

            # Собираем информацию о движении
            movement_info = {
                "user_id": user_id,
                "user_name": user_name,
                "action": action,
                "location": location,
                "shelf_id": shelf_id,
                "date": formatted_date,
                "time": formatted_time
            }
            movements.append(movement_info)

        logger.info(f"История передвижений книги получена: book_id={book_id}, movements_count={len(movements)}")
        return jsonify({"book_id": book_id, "movements": movements}), 200

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON пути книги: book_id={book_id}, error={str(e)}")
        return jsonify({"error": "Ошибка обработки истории передвижений"}), 500
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при получении истории: book_id={book_id}, error={str(e)}")
        return jsonify({"error": "Ошибка базы данных"}), 500
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении истории: book_id={book_id}, error={str(e)}")
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500