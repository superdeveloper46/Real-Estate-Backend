from flask import request, g, jsonify
import os
import jwt
from appname.models.user import User
from functools import wraps
import uuid

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Generate unique request ID in one request cycle
        g.request_id = str(uuid.uuid4())

        token = None
        if request.method == 'OPTIONS' :
            return f('', *args, **kwargs)
        
        if request.endpoint in ['auth.login', 'auth.signup', 'auth.reset_password', 'auth.request_password_reset', 'property.downloadFile']:
            return f('', *args, **kwargs)
        
        if 'Authorization' in request.headers:
            token = request.headers.get('Authorization')
            
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY'))
            current_user = User.query.filter_by(id = data['id']).first()
        except jwt.ExpiredSignatureError:
            g.uid = ''
            return jsonify({'message': 'Token has expired!'}), 401
        except Exception:
            g.uid = ''
            return jsonify({'message': 'Invalid token!'}), 401
        
        return  f(current_user, *args, **kwargs)
  
    return decorated
