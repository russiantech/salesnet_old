from os import getenv, path

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

import logging
LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOGGING_LEVEL = logging.INFO  # Adjust the log level as needed

#// APP-CONFIG
class Config:

    FLASK_APP = 'app.py'
    SECRET_KEY = getenv('seckey')
    UPLOAD_FOLDER = getenv('upload_url')
    MAX_CONTENT_PATH = None
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = getenv('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = getenv('ELASTICSEARCHURL')
    POSTS_PER_PAGE = 25
    APP_LOGO = '/static/img/favicon/favicon32x32.png'
    ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'svg', 'jpg', 'jpeg', 'gif','mp4']

    LOG_TO_STDOUT = getenv('LOG_TO_STDOUT')

    #SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/empty" #mysql(no-password set, it's supposed to come after //root:)
    OAUTHLIB_INSECURE_TRANSPORT = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = getenv('db_url', 'sqlite:///')
    SQLALCHEMY_DATABASE_ENGINE = {
    'rollback_on_exception': True,
    'autoflush': True,
    'expire_on_commit': False,
    }

    #prevents Shared Session Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # If using HTTPS
    #//
    SESSION_TYPE = 'redis' #//other-options('filesystem','mongodb') etc but'filesystem' is only suitable for small projects)
    #CACHE_TYPE = 'redis' #//other-options('simple', 'memcached', or 'filesystem')
    #CACHE_TYPE = 'simple' #//other-options('simple', 'memcached', or 'filesystem')
    REDIS_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_KEY_PREFIX': 'server_1',
    'CACHE_REDIS_HOST': 'redis://localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_URL': getenv('redis_url', 'redis://'),
    }

    #//MAIL
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    DEFAULT_MAIL_SENDER = getenv('DEFAULT_MAIL_SENDER') 
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = True
    ADMINS = ['sales@net.co', 'chrisjsmez@gmail.com']

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    FLASK_APP = 'app.py'
    MAIL_DEBUG = True
    DEFAULT_MAIL_SENDER = getenv('DEFAULT_MAIL_SENDER') 
    DEFAULT_MAIL_TOKEN = getenv('mailtrap_token') 
    MAIL_SERVER = getenv('mailtrap_server')
    MAIL_PORT = getenv('mailtrap_port')
    MAIL_USERNAME = getenv('mailtrap_username')
    MAIL_PASSWORD = getenv('mailtrap_password')
    #SQLALCHEMY_ECHO = True
    LOGGING_FORMAT = LOGGING_FORMAT
    LOGGING_LEVEL = LOGGING_LEVEL
    #//SESSION_TYPE = 'filesystem'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'production'
    MAIL_DEBUG = False
    DEFAULT_MAIL_SENDER = getenv('DEFAULT_MAIL_SENDER') 
    MAIL_SERVER = getenv('mail_server')
    MAIL_PORT = getenv('mail_port')
    MAIL_USERNAME = getenv('mail_username')
    MAIL_PASSWORD = getenv('mail_password')

    LOGGING_FORMAT = LOGGING_FORMAT
    LOGGING_LEVEL = LOGGING_LEVEL
    SQLALCHEMY_ECHO = False
    # Add production-specific settings here
    
    #prevents Shared Session Cookies #// so that other similar browsers would not have access to same first logged-in user account
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # If using HTTPS
    #//SESSION_TYPE = 'redis' # 'filesystem', 'mongodb' etc #//only suitable for small projects

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
