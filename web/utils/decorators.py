# application/decorators.py

from functools import wraps
from flask import jsonify, redirect, request, url_for, flash
from flask_login import current_user
from functools import wraps
from flask import abort
import traceback
from sqlalchemy.exc import IntegrityError
from wtforms import ValidationError

from web.models import db

def confirm_email(func):
    '''Check if email has been confirmed'''
    @wraps(func)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and not current_user.verified :
            flash(f' You\'re Yet To Verify Your Account!', 'danger')
            return redirect(url_for('auth.unverified'))
        return func(*args, **kwargs)
    return wrapper_function

def role_required(*permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                #return redirect(url_for('auth.signin')) 
                #return redirect(url_for('errors.403'))
                return redirect(url_for('auth.signin')) or abort(401) # Unauthorized/unauthenticated
                #return current_app.login_manager.unauthorized()

            is_permitted = any(permission in [permission.name for permission in current_user.permissions] for permission in permissions)
            allow_all = any( '*' in permission for permission in permissions)
            
            #return view_func(*args, **kwargs) if is_permitted else abort(403) #forbidden
            return view_func(*args, **kwargs) if is_permitted or allow_all else abort(403) #forbidden

            """ if not allow_all and not current_user.has_roles(permissions):
                abort(403)  # Forbidden """

        return wrapper
    return decorator

""" allow only admin/current_user access this routes """
def admin_or_current_user():
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.signin')) or abort(401) # Unauthorized/unauthenticated

            requested_username = kwargs.get('usrname')
            #if ( (current_user.is_admin()) | (current_user.username == usr.username) ):
            if ( (current_user.is_admin()) | (current_user.username == requested_username)  ):
                return view_func(*args, **kwargs) 
            else:
                abort(403) #forbidden

        return wrapper
    return decorator

""" only success response should have data and be set to True. And  """
response_data = {
    'success': None,
    'message': None,
    'error_message': None,
    'data': None,
    'flash': 'alert-danger', 
    'link': None ,
    'response': None
    }

def remove_chars(s: str) -> str:
    chars_to_remove = ['[', ']', '{', '}', '\'']
    for char in chars_to_remove:
        s = s.replace(char, '')
    return s
#output_str = remove_chars(input_str)

""" This works well on just deployed africana web app """
def db_session_management(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        referrer = request.headers.get('Referer')
        try:
            # Check if a transaction is already active, if not, begin a new one
            # This prevents a "transaction already started" error
            if not db.session.is_active:
                db.session.begin()

            result = route_function(*args, **kwargs)

            # Commit the transaction only if it was started in this decorator
            #I comment this bcos of  raise sa_exc.InvalidRequestError(sqlalchemy.exc.InvalidRequestError: This session is in 'committed' state; no further SQL can be emitted within this transaction.
            #cos it seems it's trying to re-commit already committed transaction in the routes.
            
            if not db.session.is_active:
                db.session.commit()

            return result

        except IntegrityError as e:
            # Handle IntegrityError (constraint violation)
            db.session.rollback()
            response_data['link'] = str(referrer),
            response_data['response'] = 'sorry, duplicates not allowed',
            response_data['errpr_message'] = f'{remove_chars(e)}',
            return jsonify(response_data)

        except Exception as e:
            # Rollback the transaction in case of any other exception
            db.session.rollback()
            
            print( f"Traceback:{traceback.format_exc()}")

            response_data['link'] = str(referrer),
            response_data['response'] = str(e),
            response_data['data'] = remove_chars(traceback.format_exc()) ,
            response_data['errpr_message'] = str(e),
            #return jsonify(response_data), 500
            return jsonify(response_data)

        finally:
            if not db.session.is_active:
                db.session.close()

    return decorated_function


""" def db_session_management(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        try:
            # Check if a transaction is already active, if not, begin a new one
            #this prevent transaction already started error
            if not db.session.is_active:
                db.session.begin()
                #db.session.begin_nested()
            
            result = route_function(*args, **kwargs)
            
            # Commit the transaction only if it was started in this decorator
            if not db.session.is_active:
                db.session.commit()
            
            return result
        
        except Exception as e:
            # Rollback the transaction in case of an exception
            db.session.rollback()
            referrer =  request.headers.get('Referer') 
            #raise
            response = {'flash': 'alert-warning', 'link': str(referrer), 'response': str(e)}
            #return jsonify(response), 500, #//with the error code 500, it's only going to return internal server error without any useful debugging informations
            return jsonify(response)
        
        finally:
            if not db.session.is_active:
                db.session.close()

    return decorated_function """

""" The decorator checks if an active transaction is already in progress using db.session.is_active. 
If no transaction is active, it starts a new one with db.session.begin(). 
It then commits the transaction only if it was started within the decorator.
This approach ensures that the decorator works seamlessly with routes that may or may not start a transaction. 
If a route has already started a transaction, the decorator won't interfere with it. 
If a route hasn't started a transaction, the decorator will start and commit one as needed. 
This way, you can use the decorator without issues regardless of the transaction state. 
//
In the provided db_session_management decorator, a finally block is not required because the decorator uses a context manager to manage the session. Context managers, 
such as the with statement, are designed to automatically handle cleanup actions like committing or rolling back resources when they go out of scope, including when exceptions occur.
//
Here's how the decorator works:

It checks if a transaction is already active using db.session.is_active.
It then enters a nested transaction using with db.session.begin_nested():. This nested transaction allows you to perform operations within the context of the current session, 
and it will be committed or rolled back automatically when the block exits.
Inside the nested transaction, it calls the route_function to perform the desired database operations.
After the with block exits, it checks whether the transaction was started by the decorator (if not is_session_active) and commits the transaction if necessary.
If an exception occurs within the with block, it automatically rolls back the transaction, and the exception is caught and handled.
The with statement ensures that the session is managed correctly, and any changes made within the block are either committed or rolled back as needed. 
Therefore, there's no need for an explicit finally block in this decorator, as the context manager takes care of it.
 """






