import os
from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret')
bcrypt = Bcrypt(app)

# connect to MongoDB Atlas
client = MongoClient(os.getenv('MONGODB_URI'))
db = client["notes_app"]


for note in db.notes.find():
    if "updated_at" not in note:
        db.notes.update_one(
            {"_id": note["_id"]},
            {"$set": {
                "updated_at": datetime.now(),
                "created_at": datetime.now()
            }}
        )

@app.route("/")
def index():
    if "email" not in session:
        return redirect("/login")

    # Fetch notes
    notes = list(db.notes.find({"email": session["email"]}))

    # Fetch user info
    user = db.users.find_one({"email": session["email"]})

    return render_template("index.html", notes=notes, user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')
        db.users.insert_one({"name": name, "email": email, "password": password})
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.users.find_one({"email": email})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["email"] = email
            return redirect("/")
    return render_template("login.html")

@app.route("/add", methods=["POST"])
def add_note():
    text = request.form["note"]
    db.notes.insert_one({
        "email": session["email"],
        "text": text,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })
    return redirect("/")

@app.route("/delete/<id>", methods=["POST"])
def delete(id):
    db.notes.delete_one({"_id": ObjectId(id)})
    return redirect("/")

@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    note = db.notes.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        new_text = request.form["note"]
        db.notes.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"text": new_text, "updated_at": datetime.now()}}
        )
        return redirect("/")

    return render_template("edit.html", note=note)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
