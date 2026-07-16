from flask import Flask,request,render_template
from flask_restful import Api,Resource
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
from wtforms import Form,StringField,validators,IntegerField
from flask_jwt_extended import create_access_token,jwt_required,get_jwt,get_jwt_identity,JWTManager
import os
client = MongoClient("localhost",27017)
db = client["3-18-flask"]
userCollection = db["user"]
productCollection = db["product"]
roleCollection = db["role"]
app =  Flask(__name__)
api = Api(app)
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"]="123456"
cors = CORS(app=app)
if len(list(roleCollection.find())) == 0:
    roleList = [
        {"name":"manager"},
        {"name":"admin"},
        {"name":"seller"},
        {"name":"customer"}
    ]
    roleCollection.insert_many(roleList)
    managerRoleId = roleCollection.find_one({"name":"manager"})["_id"]
    managerData = {
        "name":"website manager",
        "family":"lastname",
        "age":20,
        "email":"manager@gmail.com",
        "password":"12345678",
        "roleId":managerRoleId
    }
    userCollection.insert_one(managerData)

class UserValidation(Form):
    #nam
    name = StringField("name",[validators.length(min=2,max=30)])
    #family
    family = StringField("family",[validators.length(min=2,max=30),validators.Optional()])
    email = StringField("email",[validators.Email()])

    password = StringField("password",[validators.length(min=6)])

    age = IntegerField("age",[validators.number_range(min=10,max=99)])
class User(Resource):
    def post(self,id=None):
        user_validator = UserValidation(request.form)
        if user_validator.validate():
            userData  = dict(request.form)
            type_of_user  = request.args.get("type")
            if type_of_user == "seller":
                sellerRoleId = roleCollection.find_one({"name":"seller"})["_id"]
                userData["roleId"] = sellerRoleId
            elif type_of_user == "customer":
                customerRoleId = roleCollection.find_one({"name":"customer"})["_id"]
                userData["roleId"] = customerRoleId
            else:
                return {"ERROR":"WE DON't Have That Role"}
            # userData = dict(request.form)
            responseOfImage = saveImage(request.files.get("profile_pic"))
            if responseOfImage["job"] == "ok":
                userData["profileImage"] = responseOfImage["imagepath"]
            userCollection.insert_one(userData)
            return {"job":"ok"}
        else:
            return {"job":"Error","ErrorMessage":user_validator.errors}
    
    def put(self,id=None):
        updateData = dict(request.form)
        if id == None:
            return {"job":"error"}
        else:
            userCollection.update_one({"_id":ObjectId(id)},{"$set":updateData})
            return {"job":"ok"}
        
    def delete(self,id=None):
        return {"userDelete":id}
    # @jwt_required()
    def get(self,id=None):
        limit = 4
        page = request.args.get("page")
        skip = (int(page) - 1) * limit
        userlist = list(userCollection.find().skip(skip).limit(limit))
        for user in userlist:
            try:
                user["_id"] = str(user["_id"])
                user["roleId"] = str(user["roleId"])
            except KeyError:
                continue
        return {"users":userlist}


class Product(Resource):

    def post(self,id=None):
        return {"productrPost":id}
    def put(self,id=None):
        return {"productrPut":id}
    def delete(self,id=None):
        return {"productrDelete":id}
    def get(self,id=None):
        return {"productrGet":id}
    

class Login(Resource):
    def post(self):
        insertUserData = dict(request.form)
        foundedUser = userCollection.find_one({"email": insertUserData["email"]})
        if foundedUser is None:
            return {"job": "error", "errorMessage": "please sign up"}
        else:
            if foundedUser["password"] == insertUserData["password"]:
                accessToken = str(foundedUser["_id"])
                userRoleId = str(foundedUser["roleId"])
                roleName  = roleCollection.find_one({"_id":ObjectId(userRoleId)})["name"]
                role = {"role_name":roleName}
                return {"job": "ok", "accessToken": create_access_token(identity=accessToken,additional_claims=role)}
            else:
                return {"job": "error", "errorMessage": "password incorrect !"}
class Addadmin(Resource):
    @jwt_required()
    def post(self):
    
        role = dict(get_jwt())["role_name"]
        if role == "manager":
            adminData = dict(request.form)
            user_validator = UserValidation(request.form)
            if user_validator.validate():
                adminRoleId  = roleCollection.find_one({"name":"admin"})["_id"]
                adminData["roleId"] = adminRoleId
                userCollection.insert_one(adminData)
                return {"JOB":"OK"}
            else:
                return {"ERROR":user_validator.errors}
        else:
            return {"ERROR":"ACCESS DENIED"}
        

def saveImage(image):
    try:
        cwd = os.getcwd()
        folderpath = cwd + "\public"
        if not os.path.isdir(folderpath):
            os.mkdir(folderpath)
        saveImagePath = f"{folderpath}\{image.filename}"
        image.save(saveImagePath)
        return {"job":"ok","imagepath":saveImagePath}
    except Exception:
        return {"ERROR":"SOMETHING WENT WRONG"}
api.add_resource(Addadmin,"/addadmin")
api.add_resource(User,"/user","/user/<string:id>")
api.add_resource(Product,"/product","/product/<string:id>")
api.add_resource(Login,"/login")

app.run(debug=True)