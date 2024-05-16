from flask import Flask, render_template, request, redirect, flash, url_for, session, make_response, jsonify, abort
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from bson import ObjectId
from .forms import TodoForm
from application import app, db
from datetime import datetime


@app.route('/')
@app.route("/login", methods=["GET", "POST"])
def login():    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.users.find_one({"username": username, "password": password})
        
        if user:
            session['user_id'] = str(user['_id'])  # Set the user ID in the session

            # Create a JWT token
            access_token = create_access_token(identity=str(user['_id']))

            # Redirect to the appropriate page with the JWT token
            response = make_response(redirect(url_for("get_todos")))
            response.set_cookie('access_token_cookie', access_token, httponly=True, secure=False)  # Adjust secure=True in production
            return response
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))

    unique_id = request.cookies.get('unique_id')
    return render_template("login.html")

@app.route("/verify_token")
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload_files():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400, description="Invalid file extension")
            
            upload_dir = app.config['UPLOAD_PATH']
            os.makedirs(upload_dir, exist_ok=True)
            uploaded_file.save(os.path.join(upload_dir, filename))
            flash("File uploaded successfully", "success")
        return redirect(url_for('upload_files'))
    else:
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

@app.route("/todos")
@jwt_required()
def get_todos():
    current_user_id = get_jwt_identity()
    todos = []
    for todo in db.todos_flask.find({"user_id": current_user_id}).sort("date_created", -1):
        todo["_id"] = str(todo["_id"])
        todo["date_created"] = todo["date_created"].strftime("%b %d %Y %H:%M:%S")
        todos.append(todo)

    return render_template("view_todos.html", todos=todos)

@app.route("/add_todo", methods=['POST', 'GET'])
@jwt_required()
def add_todo():
    current_user_id = get_jwt_identity()
    form = TodoForm()
    if request.method == "POST":
        if form.validate_on_submit():
            todo_name = form.name.data
            todo_description = form.description.data
            completed = form.completed.data

            db.todos_flask.insert_one({
                "name": todo_name,
                "description": todo_description,
                "completed": completed,
                "date_created": datetime.utcnow(),
                "user_id": current_user_id
            })
            flash("Todo successfully added", "success")
            return redirect(url_for("get_todos"))
    return render_template("add_todo.html", form=form)

@app.route("/delete_todo/<id>")
@jwt_required()
def delete_todo(id):
    current_user_id = get_jwt_identity()
    result = db.todos_flask.find_one_and_delete({"_id": ObjectId(id), "user_id": current_user_id})
    if result:
        flash("Todo successfully deleted", "success")
    else:
        flash("Todo not found or not authorized to delete", "error")
    return redirect(url_for("get_todos"))

@app.route("/update_todo/<id>", methods=['POST', 'GET'])
@jwt_required()
def update_todo(id):
    current_user_id = get_jwt_identity()
    todo = db.todos_flask.find_one({"_id": ObjectId(id), "user_id": current_user_id})
    if not todo:
        abort(404)
    
    form = TodoForm(request.form)
    if request.method == "POST":
        # You don't need validate_on_submit() here because you're not using Flask-WTF forms
        todo_name = request.form.get("name")
        todo_description = request.form.get("description")
        completed = request.form.get("completed")

        # Update the todo
        db.todos_flask.find_one_and_update(
            {"_id": ObjectId(id), "user_id": current_user_id},
            {"$set": {
                "name": todo_name,
                "description": todo_description,
                "completed": completed,
                "date_created": datetime.utcnow()
            }})

        flash("Todo successfully updated", "success")
        return redirect(url_for("get_todos"))

    # No need for an else block here

    # Pre-populate form fields with todo data
    form.name.data = todo.get("name")
    form.description.data = todo.get("description")
    form.completed.data = todo.get("completed")

    return render_template("add_todo.html", form=form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
