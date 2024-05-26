from flask import request

def user_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip =  request.environ['REMOTE_ADDR'] or request.remote_addr
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR'] or request.headers.get('X-Forwarded-For', request.remote_addr) # if behind a proxy
    return ip