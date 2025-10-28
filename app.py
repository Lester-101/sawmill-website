import uuid
from pathlib import Path

from flask import Flask, render_template, request, url_for, send_from_directory, redirect, session

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_random_secret_key'  # important for sessions

# Define upload folder
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fixed sections
SECTIONS = ["Certificate of Appearance", "Memorandum", "Leave Form", "DTR"]

# Dummy credentials
USERNAME = "admin"
PASSWORD = "12345"   # 🔒 Change this before deployment!


# ---------- ROUTES ---------- #

@app.route('/')
def index():
    logged_in = 'user' in session
    return render_template('index.html', logged_in=logged_in)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        section = request.form['section']

        if file.filename == '' or section not in SECTIONS:
            return "Invalid selection or no file selected."

        section_path = app.config['UPLOAD_FOLDER'] / section
        section_path.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = section_path / unique_filename
        file.save(file_path)

        return f'''
        <h3>File uploaded successfully!</h3>
        <a href="{url_for('uploaded_file', section=section, filename=unique_filename)}" target="_blank">Access File</a><br>
        <a href="/view">View All Files</a>
        '''

    return render_template('upload.html')


@app.route('/uploads/<section>/<filename>')
def uploaded_file(section, filename):
    directory = str(app.config['UPLOAD_FOLDER'] / section)
    return send_from_directory(directory, filename)


@app.route('/view')
def view_files():
    files_by_section = {}
    for section in SECTIONS:
        section_path = app.config['UPLOAD_FOLDER'] / section
        if section_path.exists():
            files = [f.name for f in section_path.iterdir() if f.is_file()]
        else:
            files = []
        files_by_section[section] = files
    logged_in = 'user' in session
    return render_template('view.html', files_by_section=files_by_section, logged_in=logged_in)


@app.route('/delete/<section>/<filename>', methods=['POST'])
def delete_file(section, filename):
    if 'user' not in session:
        return redirect(url_for('login'))

    file_path = app.config['UPLOAD_FOLDER'] / section / filename
    if file_path.exists():
        file_path.unlink()
    return redirect(url_for('view_files'))


if __name__ == '__main__':
    app.run(debug=True)
