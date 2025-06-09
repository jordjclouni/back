from app import db
import datetime
from sqlalchemy.dialects.postgresql import JSONB  # Импорт JSONB

# ... (другие модели остаются без изменений)

# Таблица "books"
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(200), nullable=False)
    author_id = db.Column("author_id", db.Integer, db.ForeignKey('authors.id'), nullable=False)
    description = db.Column("description", db.Text, nullable=False)
    safe_shelf_id = db.Column("safe_shelf_id", db.Integer, db.ForeignKey('safe_shelves.id'), nullable=True)
    user_id = db.Column("user_id", db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    isbn = db.Column("isbn", db.String(13), unique=True, nullable=False)
    status = db.Column("status", db.String(50), default="available")
    path = db.Column("path", JSONB, nullable=True)  # Используем JSONB из sqlalchemy.dialects.postgresql

    reviews = db.relationship('Review', backref='book', lazy=True)
    genres = db.relationship('BookGenre', backref='book', lazy=True)

    def __repr__(self):
        return f"<Book {self.title} (ISBN: {self.isbn})>"

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "author_id": self.author_id,
            "description": self.description,
            "safe_shelf_id": self.safe_shelf_id,
            "user_id": self.user_id,
            "isbn": self.isbn,
            "status": self.status,
            "path": self.path
        }
    
# Таблица "topics"
class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(200), nullable=False)
    description = db.Column("description", db.Text, nullable=False)
    user_id = db.Column("user_id", db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column("created_at", db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='topics', lazy=True)

    def __repr__(self):
        return f"<Topic {self.title}>"

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "created_at": self.created_at.isoformat()
        }

# Таблица "messages"
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column("id", db.Integer, primary_key=True)
    content = db.Column("content", db.Text, nullable=False)
    topic_id = db.Column("topic_id", db.Integer, db.ForeignKey('topics.id'), nullable=False)
    user_id = db.Column("user_id", db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column("created_at", db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='messages', lazy=True)
    topic = db.relationship('Topic', backref='messages', lazy=True)

    def __repr__(self):
        return f"<Message {self.id} in Topic {self.topic_id}>"

    def to_json(self):
        return {
            "id": self.id,
            "content": self.content,
            "topic_id": self.topic_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "created_at": self.created_at.isoformat()
        }

# Таблица "roles"
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    functions = db.Column("functions", db.String(200), nullable=True)
    access_level = db.Column("access_level", db.String(100), nullable=True)

    users = db.relationship('User', backref='role', lazy=True)

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "functions": self.functions,
            "access_level": self.access_level
        }

# Таблица "users"
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column("user_id", db.Integer, primary_key=True)
    role_id = db.Column("role_id", db.Integer, db.ForeignKey('roles.id'), nullable=False)
    name = db.Column("name", db.String(100), nullable=False)
    email = db.Column("email", db.String(150), unique=True, nullable=False)
    password = db.Column("password", db.String(200), nullable=False)
    avatar_url = db.Column("avatar_url", db.String(200), nullable=True)
    bio = db.Column("bio", db.Text, nullable=True)
    phone = db.Column("phone", db.String(20), nullable=True)
    birth_date = db.Column("birth_date", db.Date, nullable=True)

    reviews = db.relationship('Review', backref='user', lazy=True)
    books = db.relationship('Book', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role_id": self.role_id,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "phone": self.phone,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None
        }

# Таблица "safe_shelves"
class SafeShelf(db.Model):
    __tablename__ = 'safe_shelves'
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(150), nullable=False)
    address = db.Column("address", db.String(200), nullable=False)
    hours = db.Column("hours", db.String(100), nullable=True)
    description = db.Column("description", db.Text, nullable=True)
    latitude = db.Column("latitude", db.Float, nullable=False)
    longitude = db.Column("longitude", db.Float, nullable=False)

    books = db.relationship('Book', backref='safe_shelf', lazy=True)

    def __repr__(self):
        return f"<SafeShelf {self.name}>"

# Таблица "authors"
class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(200), nullable=False)
    description = db.Column("description", db.Text, nullable=True)

    books = db.relationship('Book', backref='author', lazy=True)

    def __repr__(self):
        return f"<Author {self.name}>"



# ... (остальные модели остаются без изменений)
# Промежуточная таблица "book_genres"
class BookGenre(db.Model):
    __tablename__ = 'book_genres'
    book_id = db.Column("book_id", db.Integer, db.ForeignKey('books.id'), primary_key=True)
    genre_id = db.Column("genre_id", db.Integer, db.ForeignKey('genres.id'), primary_key=True)

# Таблица "genres"
class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), unique=True, nullable=False)

    books = db.relationship('BookGenre', backref='genre', lazy=True)

    def __repr__(self):
        return f"<Genre {self.name}>"

# Таблица "reviews"
class Review(db.Model):
    __tablename__ = 'reviews'
    book_id = db.Column("book_id", db.Integer, db.ForeignKey('books.id'), primary_key=True)
    user_id = db.Column("user_id", db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    text = db.Column("text", db.Text, nullable=False)
    rating = db.Column("rating", db.Integer, nullable=False)

    def __repr__(self):
        return f"<Review by {self.name}>"

# Таблица "user_inventory"
class UserInventory(db.Model):
    __tablename__ = 'user_inventory'
    user_id = db.Column("user_id", db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    book_id = db.Column("book_id", db.Integer, db.ForeignKey('books.id'), primary_key=True)
    added_at = db.Column("added_at", db.DateTime, default=datetime.datetime.utcnow)

    book = db.relationship('Book', backref='inventory_entries', lazy=True)

    def __repr__(self):
        return f"<UserInventory UserID: {self.user_id}, BookID: {self.book_id}>"

    def to_json(self):
        return {
            "user_id": self.user_id,
            "book_id": self.book_id,
            "book": self.book.to_json() if self.book else None,
            "added_at": self.added_at.isoformat()
        }
    



class Favorite(db.Model):
    __tablename__ = 'favorites'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Таблица "conversations" для мессенджера
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column("id", db.Integer, primary_key=True)
    sender_id = db.Column("sender_id", db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recipient_id = db.Column("recipient_id", db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column("book_id", db.Integer, db.ForeignKey('books.id'), nullable=False)
    created_at = db.Column("created_at", db.DateTime, default=datetime.datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_conversations', lazy=True)
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_conversations', lazy=True)
    book = db.relationship('Book', backref='conversations', lazy=True)

    def __repr__(self):
        return f"<Conversation {self.id} between {self.sender_id} and {self.recipient_id}>"

    def to_json(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.name if self.sender else None,
            "recipient_id": self.recipient_id,
            "recipient_name": self.recipient.name if self.recipient else None,
            "book_id": self.book_id,
            "book_title": self.book.title if self.book else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Таблица "chat_messages" для сообщений в мессенджере
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column("id", db.Integer, primary_key=True)
    content = db.Column("content", db.Text, nullable=False)
    conversation_id = db.Column("conversation_id", db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column("sender_id", db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column("created_at", db.DateTime, default=datetime.datetime.utcnow)

    sender = db.relationship('User', backref='chat_messages', lazy=True)
    conversation = db.relationship('Conversation', backref='chat_messages', lazy=True)

    def __repr__(self):
        return f"<ChatMessage {self.id} in Conversation {self.conversation_id}>"

    def to_json(self):
        return {
            "id": self.id,
            "content": self.content,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.name if self.sender else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    safe_shelf_id = db.Column(db.Integer, db.ForeignKey('safe_shelves.id'))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_json(self):
        book = db.session.get(Book, self.book_id)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'book_title': book.title if book else None,
            'safe_shelf_id': self.safe_shelf_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
class BookRequest(db.Model):
    __tablename__ = 'book_requests'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_json(self):
        sender = User.query.get(self.sender_id)
        recipient = User.query.get(self.recipient_id)
        book = Book.query.get(self.book_id)
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': book.title if book else None,
            'sender_id': self.sender_id,
            'sender_name': sender.name if sender else None,
            'recipient_id': self.recipient_id,
            'recipient_name': recipient.name if recipient else None,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }