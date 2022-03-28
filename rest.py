from flask import Flask,make_response,jsonify
from flask_restful import Api,Resource,request
from pandas import notnull
import pymongo
from bson import ObjectId
from werkzeug.utils import secure_filename
import os,gridfs
import re
import easyocr
import cv2
import threading
import jwt
from functools import wraps
from datetime import datetime,timedelta
import magic
from token import Token

app = Flask(__name__)
api = Api(app)


UPLOAD_FOLDER = f"{os.getcwd()}/flask".replace('\\','/')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'thisissecret'


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.image

fs = gridfs.GridFS(db)


q = []

# decorator for verifying the JWT
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         # jwt is passed in the request header
#         if 'Authorization' in request.headers:
#             headers = request.headers
#             bearer = headers.get('Authorization')    # Bearer YourTokenHere
#             token = bearer.split()[1]  # YourTokenHere
#         # return 401 if token is not passed
#         if not token:
#             return make_response(

#                 'Token misiing',
#                 401,
#                 {'WWW-Authenticate' : 'Basic realm ="Token missing"'}
#             )
  
#         try:
#             # decoding the payload to fetch the stored details
#             data = jwt.decode(token, app.config['SECRET_KEY'],algorithms="HS256")
#         except Exception:
#             return make_response(

#                 'Wrong token',
#                 401,
#                 {'WWW-Authenticate' : 'Basic realm ="wrong token"'}
#             )
    
#         # returns the current logged in users contex to the routes
#         return  f(*args, **kwargs)
  
#     return decorated


class login(Resource):
    def post(self):
        # creates dictionary of form data
        auth = request.headers
    
        if not auth or not auth.get('name') or not auth.get('pass'):
            # returns 401 if any email or / and password is missing
            return make_response(

                'Plese Enter Name and Password',
                401,
                {'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
            )
    
        # user = db.user.query.filter_by(email = auth.get('email')).first()
        item = db.user.find_one({"name":auth.get("name")})
    
        if not item:
            # returns 401 if user does not exist
            return make_response(
                'No such user exsists.Please check Name and Password',
                401,
                {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
            )
    
        if item.get("pass") == auth.get("pass"):
            # generates the JWT Token
            token = jwt.encode({
                'name':item.get("name"),
                'pass':item.get("pass"),
                'exp' : datetime.utcnow() + timedelta(minutes = 200)
            }, app.config['SECRET_KEY'])
    
            return make_response(jsonify({'token' : token}), 201)
        # returns 403 if password is wrong
        return make_response(
            'Wrong password',
            403,
            {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
        )
  

class UploadImage(Resource):
 
    def ocr(self):
        while len(q)>0:
            id = q[0]
            test_key = ["Name", "Father's Name", "Pancard No", "Birth Date"]
            test_value = []

            item = db.fs.files.find({"_id" :ObjectId(id)})
            for record in item:
                filepath = record['filename']
            
            # IMAGE READING
            image = cv2.imread(f"{os.getcwd()}/{filepath}".replace('\\','/'))
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            reader = easyocr.Reader(['en', 'hi'])
            result = reader.readtext(gray_img, paragraph="False", detail=0)
            text = " ".join(result)
            test_split = text.split(" ")

            # DEFINENING PATTERN

            pancard_pattern = re.compile(r'[A-Z052]{5}[0-9SOGZA७३६९]{4}[A-Z052]')
            name_pattern = re.compile('[NnIiLl][aoO0Pp][MmnN][EeOo0]')
            bdate_pattern = re.compile('\d{2}\/\d{2}\/\d{4}')


            # FIND PANCARD NUMBER

            data = pancard_pattern.search(text).group()
            pan_number = data[0:5].replace('0','O').replace('2','Z').replace('5','S').replace('8','B').replace('1','I').replace('6','G')\
                    +data[5:9].replace('O','0').replace('Z','2').replace('S','5').replace('I','1').replace('G','6').replace('A','4').replace('३','3').replace('६','6').replace('९','9')\
                    +data[9].replace('0','O').replace('2','Z').replace('5','S').replace('8','B').replace('1','I').replace('G','6')


            # FIND BIRTHDATE

            birth_date = bdate_pattern.search(text).group()


            # CHECK WETHER PANCARD PATTERN IS NEW OR OLD

            final_name = name_pattern.findall(text)
            if len(final_name) > 0:
                for i in range(2):
                    #  FOR NAMES
                    if final_name[i] in test_split:
                        index = test_split.index(final_name[i])
                        # print(index)
                        if (test_split[index + 4]).isupper():
                            name = test_split[index + 1] + " " + test_split[index + 2] + " " + test_split[index + 3] + " " + \
                                test_split[index + 4]
                        else:
                            name = test_split[index + 1] + " " + test_split[index + 2] + " " + test_split[index + 3]
                        candidate_name = " ".join(re.findall("[A-Z]+", name))
                        # print(word1)
                        test_value.append((candidate_name))
                        test_split.remove(test_split[index])


            else:
                for i in test_split:
                    if data in i[:10]:
                        pan_index = test_split.index(i)
                        test_split.insert(pan_index, "DUMMY")
                        break
                lst_capital = []
                for i in test_split:
                    if i.isupper():
                        pattern_capital = re.compile("[A-Z]+")
                        result = pattern_capital.search(i).group()
                        lst_capital.append(result)
                new_string = "".join(lst_capital)
                pattern_india = re.compile('[I][N][D][ILil][A]')
                text_india = pattern_india.search(new_string).group()
                index = lst_capital.index(text_india)
                if index < 6:
                    name = lst_capital[index + 1] + " " + lst_capital[index + 2] + " " + lst_capital[index + 3]
                    father_name = lst_capital[index + 4] + " " + lst_capital[index + 5] + " " + lst_capital[index + 6]

                else:
                    if lst_capital[5][0:3] == 'GOV':
                        name = lst_capital[3] + " " + lst_capital[4]
                    else:
                        name = lst_capital[3] + " " + lst_capital[4] + " " + lst_capital[5]

                    if lst_capital[index + 3] == "DUMMY":
                        father_name = lst_capital[index + 1] + " " + lst_capital[index + 2]
                    else:
                        father_name = lst_capital[index + 1] + " " + lst_capital[index + 2] + " " + lst_capital[index + 3]
                test_value.append(name)
                test_value.append(father_name)

            test_value.append(pan_number)
            test_value.append(birth_date)
            db.fs.files.update_one({"data": {"$exists": False}}, {"$set": {"data": dict(zip(test_key,test_value))}})
            q.remove(id)

    @token_required
    def post(self):
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        path = f'flask/{file.filename}'
        mime = magic.Magic(mime=True)
        mtype = mime.from_file((f"{os.getcwd()}/{path}").replace('\\','/'))
        db.fs.files.insert_one({'filename':path,'MimeType':mtype})    
        item = db.fs.files.find_one({'filename':path})
        id = item.get("_id")
        q.append(id)
        if len(q) == 1:
            t = threading.Thread(target=self.ocr)
            t.setDaemon(False)
            t.start()

        return {'id':f'{id}'}
            
class data(Resource):
    @token_required
    def get(self,id):
        try:
            item = db.fs.files.find_one({"_id" :ObjectId(id)})
        except:
            return "Enter Valid ID"
        if item is not None:
            try:
                name = item["data"]["Name"]
                father = item["data"]["Father's Name"]
                pan = item["data"]["Pancard No"]
                bdate = item["data"]["Birth Date"]
                return ({"Name":name,"Father's name":father,"Pancard No":pan,"Birth Date":bdate})
            except:
                return ("Plese wait. Processing your data")
        else:
            return  "Enter Valid ID"


api.add_resource(UploadImage,"/upload")
api.add_resource(data,"/<string:id>")
api.add_resource(login,"/login")

if __name__=="__main__":
    app.run(debug=True)
    