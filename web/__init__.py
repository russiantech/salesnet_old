# web/__init__.py
#from web.extensions import *
from flask import Flask

from  web.extensions import (
    confiq_app, init_ext, make_available, setup_logging
)

def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)

    # Debugging statements
    print(f"Configuring app for: {config_name}")

    confiq_app(app, config_name) #configure app, it needs the Flask instance to work

    init_ext(app) #initialize extensions. imported from extensions.py, also needs a configured Flask instance 
    
    # Debugging statements
    print("App configured and extensions initialized")
    
    app.context_processor(make_available) #make some-data available through-out
    #//blue-prints
    from web.auth.routes import auth
    from web.account.routes import acct
    from web.main.routes import main
    from web.cart.routes import cart
    from web.pays.routes import pay
    from web.endpoint.routes import endpoint
    from web.errors.handlers import errors

    # // api-blueprint(s)
    from web.apis.users import user_bp
    from web.apis.listings import listing_bp
    from web.apis.chatme import chat_api
    app.register_blueprint(user_bp)
    app.register_blueprint(listing_bp)

    #//blueprints-registration
    app.register_blueprint(auth)
    app.register_blueprint(acct)
    app.register_blueprint(main)
    app.register_blueprint(cart)
    app.register_blueprint(pay)
    app.register_blueprint(endpoint)
    app.register_blueprint(errors)

    app.register_blueprint(chat_api, url_prefix='/api')
    # error logging setup
    setup_logging(app)

    return app
