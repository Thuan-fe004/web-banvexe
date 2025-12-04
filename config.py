"""
Configuration file for the Bus Ticket System
Chứa các cấu hình database, secret key, và các hằng số
"""

import os

class Config:
    """Base configuration"""
    
    # Secret key cho Flask session
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret123'
    
    # Database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST') or 'localhost',
        'user': os.environ.get('DB_USER') or 'root',
        'password': os.environ.get('DB_PASSWORD') or '123456',
        'database': os.environ.get('DB_NAME') or 'bus_ticket',
        'autocommit': True
    }
    
    # Password hashing
    BCRYPT_LOG_ROUNDS = 12
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Admin default account
    DEFAULT_ADMIN = {
        'username': 'admin@123',
        'full_name': 'Quản trị viên hệ thống',
        'email': 'admin@system.com',
        'phone': '0000000000',
        'address': 'Hà Nội, Việt Nam',  # ← Thêm dòng này
        'password': 'Admin123@',
        'role': 'admin'
    }
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # Upload configuration (for future use)
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'bus_ticket_test',
        'autocommit': True
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}