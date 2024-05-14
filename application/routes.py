from application import app
from flask import render_template, request, redirect, flash, url_for, session, make_response, jsonify, abort
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from .forms import TodoForm
from application import db
from datetime import datetime


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.users.find_one({"username": username, "password": password})
        
        if user:
            print("Authentication successful for user:", username)
            # Set the user ID in the session
            session['user_id'] = str(user['_id'])  # Assuming user['_id'] is the user ID in your database

            # Redirect to the appropriate page
            return redirect(url_for("add_todo"))  
        else:
            print("Authentication failed for user:", username)
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))  
    else:
        print("GET request received for login page")
        return render_template("login.html")

@app.route("/verify_token")
def verify_token():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

from flask import render_template

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Handle file upload logic for POST requests
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            upload_dir = os.path.join(app.config['UPLOAD_PATH'], 'uploads')
            os.makedirs(upload_dir, exist_ok=True) 
            uploaded_file.save(os.path.join(upload_dir, filename))
            flash("File uploaded successfully", "success")
        return redirect(url_for('file_upload'))
    else:
        # Render the file upload page for GET requests
        return render_template('fileupload.html')


@app.route("/fileupload")
def file_upload():
    return render_template("fileupload.html")

@app.route('/layout')
def layout():
    return render_template('layout.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))  

        if db.users.find_one({"username": username}):
            flash("Username already exists", "error")
            return redirect(url_for("register")) 

        db.users.insert_one({
            "username": username,
            "password": password
        })

        flash("Registration successful. You can now login.", "success")
        return redirect(url_for("login")) 

    return render_template("register.html")

@app.route("/")    
def get_todos():
    todos = []
    for todo in db.todos_flask.find().sort("date_created", -1):
        todo["_id"] = str(todo["_id"])
        todo["date_created"] = todo["date_created"].strftime("%b %d %Y %H:%M:%S")
        todos.append(todo)

    return render_template("view_todos.html", todos = todos)
    

@app.route("/add_todo", methods = ['POST', 'GET'])
def add_todo():
    if request.method == "POST":
        form = TodoForm(request.form)
        todo_name = form.name.data
        todo_description = form.description.data
        completed = form.completed.data

        db.todos_flask.insert_one({
            "name": todo_name,
            "description": todo_description,
            "completed": completed,
            "date_created": datetime.utcnow()
        })
        flash("Todo successfully added", "success")
        return redirect("/")
    else:
        form = TodoForm()
    return render_template("add_todo.html", form = form)


@app.route("/delete_todo/<id>")
def delete_todo(id):
    db.todos_flask.find_one_and_delete({"_id": ObjectId(id)})
    flash("Todo successfully deleted", "success")
    return redirect("/")


@app.route("/update_todo/<id>", methods = ['POST', 'GET'])
def update_todo(id):
    if request.method == "POST":
        form = TodoForm(request.form)
        todo_name = form.name.data
        todo_description = form.description.data
        completed = form.completed.data

        db.todos_flask.find_one_and_update({"_id": ObjectId(id)}, {"$set": {
            "name": todo_name,
            "description": todo_description,
            "completed": completed,
            "date_created": datetime.utcnow()
        }})
        flash("Todo successfully updated", "success")
        return redirect("/")
    else:
        form = TodoForm()

        todo = db.todos_flask.find_one_or_404({"_id": ObjectId(id)})
        print(todo)
        form.name.data = todo.get("name", None)
        form.description.data = todo.get("description", None)
        form.completed.data = todo.get("completd", None)

    return render_template("add_todo.html", form = form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
