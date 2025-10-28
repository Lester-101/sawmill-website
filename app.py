import uuid
from pathlib import Path
from flask import Flask, render_template, request, url_for, send_from_directory, redirect, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace_this_with_a_random_secret_key")

# Define upload folder
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fixed sections
SECTIONS = ["Certificate of Appearance", "Memorandum", "Leave Form", "DTR"]

# Credentials file
CREDENTIAL_FILE = BASE_DIR / "credentials.txt"


# ---------- HELPER FUNCTIONS ---------- #

def load_credentials():
    users = []
    if CREDENTIAL_FILE.exists():
        with open(CREDENTIAL_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    users.append({"username": parts[0], "password": parts[1], "role": parts[2]})
    return users


def save_credentials(users):
    with open(CREDENTIAL_FILE, "w") as f:
        for u in users:
            f.write(f"{u['username']},{u['password']},{u['role']}\n")


def update_password(username, new_password):
    users = load_credentials()
    for u in users:
        if u["username"] == username:
            u["password"] = new_password
            break
    save_credentials(users)


# ---------- ROUTES ---------- #

@app.route('/')
def index():
    logged_in = 'user' in session
    role = session.get('role', None)
    return render_template('index.html', logged_in=logged_in, role=role)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_credentials()
        for u in users:
            if u["username"] == username and u["password"] == password:
                session['user'] = username
                session['role'] = u["role"]
                return redirect(url_for('index'))

        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        section = request.form['section']

        if file.filename == '' or section not in SECTIONS:
            error = "Please select a section and choose a file."
            return render_template('upload.html', error=error, sections=SECTIONS)

        section_path = app.config['UPLOAD_FOLDER'] / section
        section_path.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = section_path / unique_filename
        file.save(file_path)

        message = f"File uploaded successfully to '{section}' section!"
        return render_template('upload.html', message=message, sections=SECTIONS)

    return render_template('upload.html', sections=SECTIONS)


@app.route('/uploads/<section>/<filename>')
def uploaded_file(section, filename):
    directory = str(app.config['UPLOAD_FOLDER'] / section)
    return send_from_directory(directory, filename)


@app.route('/view')
def view_files():
    if 'user' not in session:
        return redirect(url_for('login'))

    files_by_section = {}
    for section in SECTIONS:
        section_path = app.config['UPLOAD_FOLDER'] / section
        if section_path.exists():
            files = [f.name for f in section_path.iterdir() if f.is_file()]
        else:
            files = []
        files_by_section[section] = files

    return render_template('view.html', files_by_section=files_by_section, role=session.get('role'))


@app.route('/delete/<section>/<filename>', methods=['POST'])
def delete_file(section, filename):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    file_path = app.config['UPLOAD_FOLDER'] / section / filename
    if file_path.exists():
        file_path.unlink()
    return redirect(url_for('view_files'))


# ---------- PASSWORD MANAGEMENT ---------- #

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('change_password.html', error="Passwords do not match.")
        else:
            update_password(username, new_password)
            return render_template('change_password.html', success="Password updated successfully!")

    return render_template('change_password.html')


@app.route('/admin/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = load_credentials()

    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        update_password(username, new_password)
        return render_template('manage_users.html', users=users, success=f"Password updated for {username}")

    return render_template('manage_users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
