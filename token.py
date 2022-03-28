from flask import Flask,make_response,jsonify
from flask_restful import Api,Resource,request
import jwt
from functools import wraps
from datetime import datetime,timedelta

# decorator for verifying the JWT
class Token():
    def token_required(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            # jwt is passed in the request header
            if 'Authorization' in request.headers:
                headers = request.headers
                bearer = headers.get('Authorization')    # Bearer YourTokenHere
                token = bearer.split()[1]  # YourTokenHere
            # return 401 if token is not passed
            if not token:
                return make_response(

                    'Token misiing',
                    401,
                    {'WWW-Authenticate' : 'Basic realm ="Token missing"'}
                )
    
            try:
                # decoding the payload to fetch the stored details
                data = jwt.decode(token, 'thisissecret',algorithms="HS256")
            except Exception:
                return make_response(

                    'Wrong token',
                    401,
                    {'WWW-Authenticate' : 'Basic realm ="wrong token"'}
                )
        
            # returns the current logged in users contex to the routes
            return  f(*args, **kwargs)
    
        return decorated


