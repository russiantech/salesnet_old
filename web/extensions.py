# web/extensions.py
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from os import getenv
from web.apis.tokens import hash_auth
#from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
#from flask_session import Session
#from flask_oauthlib.client import OAuth //flask_oauth not actively maintained
from authlib.integrations.flask_client import OAuth

from flask_caching import Cache
from flask_limiter import Limiter
from elasticsearch import Elasticsearch
from flask_socketio import SocketIO
from redis import Redis
from flask import request
from blinker import Namespace
from web.models import db, Category, User

from web.utils import categorylist
from web.account.forms import PostForm
from web.utils.custom_mixins import SearchForm
from web.auth.forms import SignupForm

from config import Config 
#print(Config.REDIS_CONFIG)

load_dotenv() #load-env-variables.

#db = SQLAlchemy(app)
csrf = CSRFProtect()
#f_session = Session()
bcrypt = Bcrypt()
s_manager = LoginManager()
mail = Mail()
migrate = Migrate()
moment = Moment()
oauth = OAuth()
signals = Namespace()

redis = Redis.from_url(getenv('redis_url', 'redis://'))
#limiter = Limiter(key_func=lambda: 'global', storage_uri=getenv('redis_url')) 
#socketio = SocketIO()
#socketio = SocketIO(manage_session=False, async_mode='threading', cors_allowed_origins="*")
#socketio = SocketIO(app, message_queue=app.config['REDIS_URL'])
#socketio = SocketIO(manage_session=False, message_queue=getenv('redis_url', 'redis://'), cors_allowed_origins="*")
socketio = SocketIO(manage_session=False, cors_allowed_origins="*")
#redis = Redis(host='localhost', port=6379)

limiter = Limiter(
    storage_uri=getenv('redis_url'),
    key_func=lambda: request.remote_addr,
)
#cache = Cache()
cache = Cache(config=Config.REDIS_CONFIG)

s_manager.login_view = 'auth.signin'
@s_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def setup_logging(app):
    if not app.debug:
        formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=10)
        handler.setLevel(app.config['LOGGING_LEVEL'])
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    
def make_available():
    # Load categories
    num_categories_to_load = 150
    q_categories = Category.query.order_by(Category.id.asc()).limit(num_categories_to_load).all()
    categories = categorylist.build_category_tree(q_categories) 

    print(categories)
    # Create instances of PostForm and SearchForm
    
    # Create a context dictionary with the variables you want to make available
    app_data = {
        'app_name': 'Salesnet.',
        'app_desc': 'Internet of sales. Salesnet is a mordern social sales & connection technologies. \
        A product of Techa. Techa aims to power sales for business(es) and empower people using mordern technologies.',
        'app_location': 'lekki, lagos, nigeria.',
        'app_email': 'hi@salesnet.co',
        'app_logo': getenv('logo_url'),
        # Add other data like logo URL
    }

    context = {
        'categories': categories or { },
        'postform': PostForm(),
        'searchform': SearchForm(),
        'signupform': SignupForm(),
        'hash_auth': hash_auth,
        **app_data #merge the 2 using dictionary unpacking ** operator.
    }
    

    return context

def init_ext(app):
    db.init_app(app)
    csrf.init_app(app)
    #f_session.init_app(app) #enable this on cpanel for file-session type, good alternative is redis-server instead.
    bcrypt.init_app(app)
    s_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)
    #socketio.init_app(app, manage_session=False, async_mode='threading', cors_allowed_origins="*")
    socketio.init_app(app)
    #cache.init_app(app, config=app.config['REDIS_CONFIG'])
    cache.init_app(app)
    #cache.init_app(app)

def confiq_app(app, config_name):
    from config import app_config
    app.config.from_object(app_config[config_name])
    app.elasticsearch = Elasticsearch([getenv('elasticsearch_url')]) # Create an Elasticsearch client instance

    """ if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'development':
        app.config.from_object('config.DevelopmentConfig') """
    
    