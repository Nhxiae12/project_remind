from datetime import datetime
import os
from flask import (
    Flask,
    flash,
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
    <link rel="manifest" href="/static/manifest.json">
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
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/sw.js');
        });
      }
    </script>
</body>
</html>
"""

REGISTER_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Project REMIND - Register</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#212529">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand">Project REMIND - Registration</span>
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
        <div class="row justify-content-center mt-4">
            <div class="col-md-5">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="text-center mb-4">Create Personnel Account</h3>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Role / Responsibility</label>
                                <select name="role" class="form-select" required>
                                    <option value="Staff">Staff (Submits & Uploads Reports)</option>
                                    <option value="Coordinator">Coordinator (Views & Monitors Reports)</option>
                                    <option value="Official">Official (Municipal Reviewer)</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Office / Barangay Name</label>
                                <input type="text" name="office" class="form-control" placeholder="e.g. Barangay Pinaripad Sur" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Register Account</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/login">Already have an account? Login here</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/sw.js');
        });
      }
    </script>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Project REMIND - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#212529">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark px-4 mb-4">
        <span class="navbar-brand">Project REMIND Dashboard</span>
        <div>
            <span class="text-light me-3">User: <strong>{{ user.username }}</strong> ({{ user.role }} - {{ user.office }})</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
        </div>
    </nav>
    <div class="container-fluid px-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <h2 class="mb-4">Reporting and Monitoring Overview</h2>

        <div class="row">
            <!-- Staff Submit / Upload Report Form -->
            {% if user.role == 'Staff' %}
            <div class="col-md-5 mb-4">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">Create New Report Task</div>
                    <div class="card-body">
                        <form method="POST" action="/create_task" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label class="form-label">Report Title</label>
                                <input type="text" name="title" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description / Guidelines</label>
                                <textarea name="description" class="form-control" rows="3" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Deadline</label>
                                <input type="date" name="deadline" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Assigned Office / Barangay</label>
                                <input type="text" name="office_assigned" class="form-control" value="{{ user.office }}" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Upload File for Submission</label>
                                <input type="file" name="report_file" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Publish Task</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Coordinator / Official View: Monitoring Table -->
            {% if user.role == 'Coordinator' or user.role == 'Official' %}
            <div class="col-md-12">
                <div class="card shadow">
                    <div class="card-header bg-secondary text-white">Active Report Assignments</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered align-middle">
                                <thead class="table-light">
                                    <tr>
                                        <th>Task / Report</th>
                                        <th>Office Assigned</th>
                                        <th>Deadline</th>
                                        <th>Status</th>
                                        <th>Submission Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in tasks %}
                                    <tr>
                                        <td>
                                            <strong>{{ task.title }}</strong><br>
                                            <small class="text-muted">{{ task.description }}</small>
                                        </td>
                                        <td>{{ task.office_assigned }}</td>
                                        <td>{{ task.deadline }}</td>
                                        <td>
                                            <span class="badge bg-info text-dark">Submitted</span>
                                        </td>
                                        <td>
                                            <span class="text-success fw-bold small">Submitted on: {{ task.submitted_at }}</span><br>
                                            <small class="text-dark"><strong>File:</strong> {{ task.submission_details }}</small>
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="5" class="text-center text-muted">
                                            No report tasks available yet.
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/sw.js');
        });
      }
    </script>
</body>
</html>
"""


# --- ROUTES ---


@app.route('/')
def index():
  return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
      session['user_id'] = user.id
      flash('Logged in successfully!', 'success')
      return redirect(url_for('dashboard'))
    else:
      flash('Invalid username or password.', 'danger')

  return render_template_string(LOGIN_PAGE)


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    office = request.form['office']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
      flash('Username already taken. Choose another.', 'danger')
    else:
      new_user = User(
          username=username,
          password=generate_password_hash(password),
          role=role,
          office=office,
      )
      db.session.add(new_user)
      db.session.commit()
      flash(
          'Account successfully created! You can now log in.',
          'success',
      )
      return redirect(url_for('login'))

  return render_template_string(REGISTER_PAGE)


@app.route('/dashboard')
def dashboard():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  user = User.query.get(session['user_id'])
  tasks = Task.query.all()
  return render_template_string(DASHBOARD_PAGE, user=user, tasks=tasks)


@app.route('/create_task', methods=['POST'])
def create_task():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  user = User.query.get(session['user_id'])
  if user.role != 'Staff':
    flash('Unauthorized action.', 'danger')
    return redirect(url_for('dashboard'))

  title = request.form['title']
  description = request.form['description']
  deadline = request.form['deadline']
  office_assigned = request.form['office_assigned']

  filename = 'No file uploaded'
  if 'report_file' in request.files:
    file = request.files['report_file']
    if file and file.filename != '':
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

  new_task = Task(
      title=title,
      description=description,
      deadline=deadline,
      office_assigned=office_assigned,
      status='Submitted',
      submission_details=filename,
      submitted_at=datetime.now().strftime('%Y-%m-%d %H:%M'),
  )
  db.session.add(new_task)
  db.session.commit()
  flash('Report successfully submitted and uploaded!', 'success')
  return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
  session.pop('user_id', None)
  flash('Logged out successfully.', 'info')
  return redirect(url_for('login'))


# --- DATABASE INITIALIZATION ---
with app.app_context():
  db.create_all()
  default_users = [
      ('coordinator_admin', 'Coordinator', 'Municipal Office'),
      ('barangay_secretary', 'Staff', 'Barangay Pinaripad Sur'),
      ('municipal_mayor', 'Official', 'Municipal Hall'),
  ]
  for uname, urole, uoffice in default_users:
    if not User.query.filter_by(username=uname).first():
      u = User(
          username=uname,
          password=generate_password_hash('password123'),
          role=urole,
          office=uoffice,
      )
      db.session.add(u)
  db.session.commit()

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
