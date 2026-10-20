import os
from flask import (
    Flask, render_template_string, request, redirect, url_for, 
    session, flash, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'project-remind-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'Staff', 'Coordinator', 'Official'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    barangay = db.Column(db.String(100), nullable=False)
    submitted_by = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default='Submitted')

with app.app_context():
    db.create_all()
    # Create default accounts if none exist
    if not User.query.filter_by(username='staff1').first():
        db.session.add(User(username='staff1', password_hash=generate_password_hash('password123'), role='Staff'))
        db.session.add(User(username='coord1', password_hash=generate_password_hash('password123'), role='Coordinator'))
        db.session.add(User(username='official1', password_hash=generate_password_hash('password123'), role='Official'))
        db.session.commit()

# Direct Routes for PWABuilder & PWA Assets
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory('static', 'logo.png', mimetype='image/png')

# HTML Templates
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project REMIND</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1a202c">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f7fafc; color: #2d3748; margin: 0; padding: 0; }
        header { background: #2b6cb0; color: white; padding: 1rem; text-align: center; font-size: 1.25rem; font-weight: bold; }
        .container { max-width: 800px; margin: 2rem auto; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .btn { background: #3182ce; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #2b6cb0; }
        .btn-danger { background: #e53e3e; }
        .btn-danger:hover { background: #c53030; }
        input, select, textarea { width: 100%; padding: 0.5rem; margin-top: 0.25rem; margin-bottom: 1rem; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }
        th { background: #edf2f7; }
        .flash { padding: 0.75rem; margin-bottom: 1rem; background: #fed7d7; color: #9b2c2c; border-radius: 4px; }
    </style>
</head>
<body>
    <header>
        Project REMIND
        {% if session.get('user_id') %}
            <span style="font-size: 0.9rem; font-weight: normal; float: right;">
                Role: {{ session.get('role') }} | <a href="/logout" style="color: white;">Logout</a>
            </span>
        {% endif %}
    </header>
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('Service Worker registered!'))
                    .catch(err => console.log('Service Worker registration failed:', err));
            });
        }
    </script>
</body>
</html>
"""

LOGIN_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<h2>Login</h2>
<form method="POST">
    <label>Username</label>
    <input type="text" name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <button type="submit" class="btn">Login</button>
</form>
""")

DASHBOARD_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<h2>Welcome, {{ session['username'] }} ({{ session['role'] }})</h2>

{% if session['role'] == 'Staff' %}
    <h3>Submit New Report</h3>
    <form method="POST" action="/submit_report" enctype="multipart/form-data">
        <label>Report Title</label>
        <input type="text" name="title" required>
        <label>Barangay Designation</label>
        <input type="text" name="barangay" required>
        <label>Attach File (optional)</label>
        <input type="file" name="file">
        <button type="submit" class="btn">Submit Report</button>
    </form>
{% endif %}

<h3>Monitoring Table</h3>
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Barangay</th>
            <th>Submitted By</th>
            <th>Status</th>
            <th>Attachment</th>
        </tr>
    </thead>
    <tbody>
        {% for report in reports %}
        <tr>
            <td>{{ report.id }}</td>
            <td>{{ report.title }}</td>
            <td>{{ report.barangay }}</td>
            <td>{{ report.submitted_by }}</td>
            <td>{{ report.status }}</td>
            <td>
                {% if report.filename %}
                    <a href="/uploads/{{ report.filename }}" target="_blank">View File</a>
                {% else %}
                    None
                {% endif %}
            </td>
        </tr>
        {% else %}
        <tr>
            <td colspan="6" style="text-align: center;">No reports submitted yet.</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
""")

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    reports = Report.query.all()
    return render_template_string(DASHBOARD_HTML, reports=reports)

@app.route('/submit_report', methods=['POST'])
def submit_report():
    if 'user_id' not in session or session.get('role') != 'Staff':
        return redirect(url_for('login'))
    
    title = request.form['title']
    barangay = request.form['barangay']
    file = request.files.get('file')
    filename = None
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
    new_report = Report(
        title=title,
        barangay=barangay,
        submitted_by=session['username'],
        filename=filename
    )
    db.session.add(new_report)
    db.session.commit()
    flash('Report submitted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
