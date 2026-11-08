from datetime import datetime
import os
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'project_remind_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remind.db'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)


# --- DATABASE MODELS ---
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(200), nullable=False)
  role = db.Column(db.String(50), nullable=False)  # Coordinator, Staff, Official
  office = db.Column(db.String(100), nullable=False)


class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(150), nullable=False)
  description = db.Column(db.Text, nullable=False)
  deadline = db.Column(db.String(50), nullable=False)
  office_assigned = db.Column(db.String(100), nullable=False)
  status = db.Column(db.String(50), default='Submitted')
  submission_details = db.Column(db.Text, nullable=True)
  submitted_at = db.Column(db.String(50), nullable=True)


# --- HTML TEMPLATES ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Project REMIND - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#212529">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand">Project REMIND</span>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <div class="row justify-content-center mt-5">
            <div class="col-md-4">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="text-center mb-4">Personnel Login</h3>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/register">Need an account? Register here</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
      if ('serviceWorker' in navigator) {
    
