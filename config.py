import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Güvenlik
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'satranc-turnuva-secret-key-2024'

    # Veritabanı
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(basedir, 'instance', 'chess.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Koruması (Flask-WTF)
    WTF_CSRF_ENABLED = True

    # Sayfalama
    TOURNAMENTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    TOKENS_PER_PAGE = 25

    # Flask-Login
    LOGIN_MESSAGE = 'Bu sayfaya erişmek için lütfen giriş yapın.'
    LOGIN_MESSAGE_CATEGORY = 'warning'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False  # SQL sorgularını loglamak için True yap


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False           # Test sırasında CSRF devre dışı
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False
    # Production'da SECRET_KEY ortam değişkeninden gelmeli
    # DATABASE_URL ortam değişkeninden gelmeli


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
