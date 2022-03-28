from flask_restful import Resource,request
from flask import Flask,jsonify,request,make_response
from flask_restful import Api
import gridfs
import pymongo
import jwt,uuid
from datetime import datetime,timedelta
from bson import ObjectId
import json
from functools import wraps

app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = 'your secret key'
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.image

# decorator for verifying the JWT
def token_required(f):
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
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms="HS256")
            print (data)
        except Exception:
            return make_response(

                'Wrong token',
                401,
                {'WWW-Authenticate' : 'Basic realm ="wrong token"'}
            )
    
        # returns the current logged in users contex to the routes
        return  f(*args, **kwargs)
  
    return decorated


class login(Resource):
    def post(self):
        # creates dictionary of form data
        auth = request.headers
    
        if not auth or not auth.get('name') or not auth.get('pass'):
            # returns 401 if any email or / and password is missing
            return make_response(

                'Could not verify1',
                401,
                {'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
            )
    
        # user = db.user.query.filter_by(email = auth.get('email')).first()
        item = db.user.find_one({"name":auth.get("name")})
    
        if not item:
            # returns 401 if user does not exist
            return make_response(
                'Could not verify2',
                401,
                {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
            )
    
        if item.get("pass") == auth.get("pass"):
            # generates the JWT Token
            token = jwt.encode({
                'name':item.get("name"),
                'pass':item.get("pass"),
                'exp' : datetime.utcnow() + timedelta(minutes = 30)
            }, app.config['SECRET_KEY'])
    
            return make_response(jsonify({'token' : token}), 201)
        # returns 403 if password is wrong
        return make_response(
            'Could not verify3',
            403,
            {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
        )
  
class data(Resource):
    @token_required
    def get(self):
        return jsonify({"key":"value"})


api.add_resource(login,"/login")
api.add_resource(data,"/data")

if __name__ =="__main__":
    app.run(debug=True)

