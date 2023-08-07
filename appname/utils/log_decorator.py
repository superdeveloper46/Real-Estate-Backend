from functools import wraps
from flask import current_app, request, g

def log_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        current_app.logger.info(dict(
            request_id=g.get('request_id', 'N/A'),
            path=request.full_path,
            body=request.get_json(),
        ))
        return result
    return decorated_function
