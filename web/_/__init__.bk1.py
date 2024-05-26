

#from web.models Role, Brand
import logging
from logging.handlers import RotatingFileHandler
from os import environ
from flask import Flask, g
from elasticsearch import Elasticsearch
# web/__init__.py
from web.extensions import db, s_manager, cache, oauth, csrf, migrate, moment, bcrypt, mail
from web.utils import categorylist

from web.models import Cate
from web.account.forms import PostForm
from web.utils.search import SearchForm

from config import app_config
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

def setup_logging(app):
    if not app.debug:
        formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=10)
        handler.setLevel(app.config['LOGGING_LEVEL'])
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    
@app.before_request
def fetch_data():
    # Fetch data from the database
    num_categories_to_load = 150
    q_categories = (Cate.query.order_by(Cate.id.asc()).limit(num_categories_to_load).all())
    g.categories = categorylist.build_category_tree(q_categories)


""" # Create a context processor to make the form available everywhere
@app.context_processor
def inject_form():
    form = MyForm()
    return dict(form=form)

@app.context_processor
def context_processor():
    context_dict = {'g.categories': g.categories} if hasattr(g, 'data') else {}

    return context_dict """

@app.context_processor
def inject_context():
    #Postform = PostForm()
    context_dict = { 
        'postform': PostForm(), 
        'g.categories': g.categories} if hasattr(g, 'data')\
        else {
            'postform': PostForm(), 
            'searchform':SearchForm()
              }
    
    return context_dict

# Access the Elasticsearch URL from environment variables
#elasticsearch_url = app.config['ELASTICSEARCH_URL']
es_url = environ.get('elasticsearch_url')
# Create an Elasticsearch client instance
es = Elasticsearch([es_url])

# Test the connection
if es.ping():
    print("Connected to Elasticsearch")
else:
    print("Could not connect to Elasticsearch")

def create_app(config_name):
    app.config.from_object(app_config[config_name])
    #app.config.from_pyfile('../instance/config.py')
    #from web.models import  db, s_manager, Role, Brand
    """ app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None """
    #app.elasticsearch = es
    
    with app.app_context():

        """ app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None """

        # List available indices
        """ indices = app.elasticsearch.indices.get_alias("*")
        print(indices) """
        app.elasticsearch = es

        csrf.init_app(app)
        db.init_app(app)
        bcrypt.init_app(app)
        s_manager.init_app(app)
        cache.init_app(app)
        mail.init_app(app)
        migrate.init_app(app, db)
        moment.init_app(app)
        oauth.init_app(app)
        #api.init_app(app)
        #         
        db.create_all()

    #blue-prints
    from web.auth.routes import auth
    from web.account.routes import acct
    from web.main.routes import main
    from web.cart.routes import cart
    from web.pays.routes import pay
    from web.endpoint.routes import endpoint
    from web.errors.handlers import errors

    #blueprints-registration
    app.register_blueprint(auth)
    app.register_blueprint(acct)
    app.register_blueprint(main)
    app.register_blueprint(cart)
    app.register_blueprint(pay)
    app.register_blueprint(endpoint)
    app.register_blueprint(errors)

    #sign-in/login configuration
    s_manager.login_view = 'auth.signin'
    
    app.app_context().push() #allows-me-perform-database-operations-outside-of-view-functions/routes

    # error logging setup
    setup_logging(app)

    return app
