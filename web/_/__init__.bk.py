

#from web.models Role, Brand
from flask import Flask, g
# web/__init__.py
from web.extensions import db, s_manager, cache, oauth, csrf, migrate, moment, bcrypt, mail
from web.utils import categorylist, slug, calc_percent, activelink

from web.models import Cate
from  sqlalchemy.sql.expression import func

from config import app_config
from dotenv import load_dotenv
load_dotenv()

def setup_logging(app):
    if not app.debug:
        formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=10)
        handler.setLevel(app.config['LOGGING_LEVEL'])
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

#print(app_config['development'])

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(app_config[config_name])
    #app.config.from_pyfile('../instance/config.py')
    #from web.models import  db, s_manager, Role, Brand
    with app.app_context():

        db.init_app(app)
        bcrypt.init_app(app)
        s_manager.init_app(app)
        cache.init_app(app)
        mail.init_app(app)
        migrate.init_app(app, db)
        moment.init_app(app)
        csrf.init_app(app)
        oauth.init_app(app)
        #api.init_app(app)
        
        db.create_all()

    app.jinja_env.filters['categorylist'] = categorylist.categorylist
    app.jinja_env.filters['slugify'] = slug.slugify

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
    
    @app.before_request
    def load_random_categories():
        num_categories_to_load = 150
        random_categories = (
            Cate.query.order_by(func.rand())  # Use func.rand() for MySQL, func.random() for PostgreSQL
            .limit(num_categories_to_load)
            .all()
        )
        #g.categories = ''
        g.categories = categorylist.build_category_tree(random_categories)

    @app.context_processor
    def inject_random_categories():
        #return dict(random_categories=g.random_categories)
        #return g.categories
        num_categories_to_load = 150
        random_categories = (
            Cate.query.order_by(func.rand())  # Use func.rand() for MySQL, func.random() for PostgreSQL
            .limit(num_categories_to_load)
            .all()
        )
        #g.categories = ''
        g.categories = categorylist.build_category_tree(random_categories)

    """ @app.before_request
    def load_random_categories():
        num_categories_to_load = 83  # Change this to the number of categories you want to load
        g.random_categories = (
            db.session.query(Category)
            .order_by(func.random())  # Use func.random() for PostgreSQL
            .limit(num_categories_to_load)
            .all()
        )

    @app.context_processor
    def inject_random_categories():
        return dict(random_categories=g.random_categories) """

    app.app_context().push() #allows-me-perform-database-operations-outside-of-view-functions/routes

    # error logging setup
    setup_logging(app)

    return app
