from flask import Blueprint, render_template, request
from flask_limiter.util import get_remote_address
from web.extensions import limiter

from sqlalchemy.exc import InterfaceError

errors = Blueprint('errors', __name__)

from web.models import db
from web.apis.errors import error_response as api_error_response

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

@errors.app_errorhandler(404)
def error_404(error):
    """ Not found error """
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.html', e=error), 404

@errors.app_errorhandler(403)
def error_403(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(403)
    return render_template('errors/403.html', e=error), 403

@errors.app_errorhandler(500)
def error_500(error):
    """ Internal server error """
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html', e=error), 500

@errors.app_errorhandler(413)
def error_413(error):
    return render_template('errors/413.html', e=error), 413

@errors.app_errorhandler(429)
#@limiter.request_filter
def error_429(error):
    """ Too many request error """
    db.session.rollback()
    if wants_json_response():
        return api_error_response(429)
    return render_template('errors/429.html', e=error, client = get_remote_address()), 429 


@errors.app_errorhandler(InterfaceError or 2003)
def handle_interface_error(error):
    """ The error code 2003 in this context indicates that the MySQL client couldn't connect to the MySQL server. """
    print("Caught an InterfaceError:", error)
    db.session.rollback()
    if wants_json_response():
        return api_error_response(2003)
    return render_template('errors/2003.html', e=error, client = get_remote_address()), 2003 

    # Rest of your error handling logic


