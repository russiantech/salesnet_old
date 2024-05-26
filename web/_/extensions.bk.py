# web/extensions.py

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_oauthlib.client import OAuth
from calendar import month_abbr

from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_moment import Moment

from config import app_config

from dotenv import load_dotenv
load_dotenv()

""" db = SQLAlchemy()
migrate = Migrate()
s_manager = LoginManager()
cache = Cache()
bcrypt = Bcrypt()
mail = Mail()
moment = Moment()
csrf = CSRFProtect()
oauth = OAuth() """

app = Flask(__name__)

with app.app_context():
    app.config.from_object(app_config[config_name])
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    s_manager = LoginManager(app)
    cache = Cache(app)
    bcrypt = Bcrypt(app)
    mail = Mail(app)
    moment = Moment(app)
    csrf = CSRFProtect(app)
    oauth = OAuth(app)
    """ db.init_app(app)
    bcrypt.init_app(app)
    s_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    #api.init_app(app) """
    
    db.create_all()

@s_manager.user_loader
def load_user(uid):
    # Load the user from the session or wherever you store user information
    # and store it in the "g" object for the current request
    g.user = User.query.get(int(uid))  # Replace with your user loading logic
    return g.user