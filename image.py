from flask import Flask
from flask_restful import Api,Resource,reqparse,request
import pymongo,json,werkzeug
from bson import ObjectId
import pymongo
import base64
import bson
from bson.binary import Binary
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
api = Api(app)


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.image
collection = db.image_details

parse = reqparse.RequestParser()
parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
# file_used = "C:/Users/romil/Downloads/WhatsApp Image 2020-04-01 at 11.19.04 AM.jpeg"

# class JSONEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, ObjectId):
#             return str(o)
#         return json.JSONEncoder.default(self, o)

class UploadImage(Resource):
    def post(self):
        file = request.files['file']
        file_used = secure_filename(file.filename)
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file))

        # with open(file_used, "rb") as f:
            # encoded = Binary(f.read())

        collection.insert_one({"filename": file_used, "file": file, "description": "test" })

# class database(Resource):
#     def post(self):
#         data = request.get_json()
#         # list.append(data)
#         collection.insert_one(data)
#         return JSONEncoder().encode(data)

#     def get(self):
#         return {"key":"value"}



# api.add_resource(database,"/")
api.add_resource(UploadImage,"/upload")

if __name__=="__main__":
    app.run(debug=True)