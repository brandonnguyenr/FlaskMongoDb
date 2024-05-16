from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config["SECRET_KEY"] = "apple"
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config["MONGO_URI"] = "mongodb+srv://brandonnguyen:12345@cluster0.vygd1e8.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&appName=Cluster0"
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.JPG']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = True  
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  

mongodb_client = PyMongo(app)
jwt = JWTManager(app)
db = mongodb_client.db

from application import routes