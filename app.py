from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
import config
from weasyprint import HTML
import os
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY




PDF_OPTIONS = {
    "page-size": "A4",
    "encoding": "UTF-8",
    "enable-local-file-access": None
}


client = MongoClient(config.MONGO_URI)
db = client["school_report_card_db"]

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class Professor(UserMixin):
    def __init__(self, prof_doc):
        self.id = str(prof_doc["_id"])
        self.email = prof_doc["email"]
        self.name = prof_doc["name"]

@login_manager.user_loader
def load_user(user_id):
    prof = db.professors.find_one({"_id": ObjectId(user_id)})
    if not prof:
        return None
    return Professor(prof)

# import routes AFTER app, db, etc. are defined
from routes_auth import *
from routes_student import *

if __name__ == "__main__":
    app.run(debug=True)
