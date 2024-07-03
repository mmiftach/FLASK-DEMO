from flask import Flask, render_template, redirect, request, session, request, flash, send_from_directory,render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, login_required, logout_user
from model import db, User, Contact

import pandas as pd
import shutil
import os


# Assuming filterAccount is a function that takes a list of data
from functionFilterAccount import filterAccount
from functionRevokeAdminhub import revokeListJira

app = Flask(__name__)
app.secret_key = 'ba1a2a5a16902566850db7125beadd8c'

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



# Initialize the database
db.init_app(app)
migrate = Migrate(app, db)
admin = Admin(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Create admin views for your models
class UserModelView(ModelView):
    can_delete = False
    column_searchable_list = ['username']
    column_filters = ['username']

admin.add_view(UserModelView(User, db.session))
admin.add_view(ModelView(Contact, db.session))
# Define user loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# Use It When You Want To Add Auth To A Page
@login_required

# Happy Coding!
@app.route('/')
def index():


    return render_template('index.html')









@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Login user using Flask-Login's login_user function
            login_user(user)
            # Redirect the user back to the originally requested page (if any)
            next_page = request.args.get('next')
            return redirect(next_page or '/index')

        flash('Invalid username or password. Please try again.', 'error')
        return redirect('/login')

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/Reg', methods=['GET', 'POST'])
def Reg():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect('/Reg')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect('/login')
    return render_template('Reg.html')



# @app.route('/submit', methods=['POST'])
# def submit():
#     name = request.form['name']
#     email = request.form['email']
#     message = request.form['message']
    
#     contact = Contact(name=name, email=email, message=message)
#     db.session.add(contact)
#     db.session.commit()
    
#     return redirect('/')


@app.route('/jiraRevoker', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Delete all files in the UPLOAD_FOLDER before saving the new file
            delete_files_in_directory(app.config['UPLOAD_FOLDER'])
            filename = 'export-users.csv'  # Renamed file to export-users.csv
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            processed_filename, table_html = process_file(filepath)
            download_link = f'<a href="/download/{os.path.basename(processed_filename)}" class="btn btn-primary">Download Processed File</a>'
            return f'''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Jira Revoker - Processed Data</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    .table td, .table th {{
                        text-align: center;
                        border: 1px solid #dee2e6;
                    }}
                </style>
            </head>
            <body>
            <div class="container mt-5">
                <h1>Jira Revoker</h1>
                <div class="card">
                <div class="card-header">
                    Processed Data
                </div>
                <div class="card-body">
                    {table_html}
                </div>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            '''
        else:
            flash('File type not allowed')
            return redirect(request.url)
    return '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Jira Revoker - Upload CSV</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container mt-5">
        <h1>Jira Revoker</h1>
        <div class="card">
          <div class="card-header">
            Upload CSV File
          </div>
          <div class="card-body">
            <form method="post" enctype="multipart/form-data">
              <div class="mb-3">
                <input type="file" name="file" class="form-control">
              </div>
              <button type="submit" class="btn btn-primary">Upload</button>
            </form>
          </div>
        </div>
      </div>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/revoke/<filename>', methods=['POST'])
def revoke_admin(filename):
    # Construct the filepath for the processed file
    processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(processed_filepath)
    # Assume revokeListJira returns a list of dictionaries, e.g., [{'user': 'john_doe', 'status': 'Revoked'}, ...]
    results = revokeListJira(processed_filepath)
    print(results)
    flash('Users have been successfully revoked')

   # Assuming the 'results' variable is already defined as shown
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revoke Complete</title>
        <!-- Include Bootstrap CSS from CDN -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="mb-3 text-center">Revoke Operation Completed</h1>
            <p class="mb-3 text-center">Users have been successfully revoked. See the results below:</p>
            <!-- Apply Bootstrap table styling -->
            <table class="table table-bordered">
                <thead class="thead-light">
                    <tr>
                        <th class="text-center">Username</th>
                        <th class="text-center">Email</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in results %}
                    <tr>
                        <td class="text-center">{{ row[1] }}</td>
                        <td class="text-center">{{ row[2] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <!-- Back to Home button -->
            <div class="text-center mt-4">
                <a href="/" class="btn btn-primary">Back to Home</a>
            </div>
        </div>
        <!-- Optional JavaScript and jQuery for Bootstrap components -->
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.2/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    ''', results=results)

def process_file(filepath):
    data = pd.read_csv(filepath)
    filtered_data = filterAccount(data)  # Assuming filterAccount now returns a DataFrame
    processed_filename = filepath.rsplit('.', 1)[0] + '_processed.csv'  # Append '_processed' to the original filename
    filtered_data.to_csv(processed_filename, index=False)  # Save the processed file
    
    # Wrap the table in a div with class 'table-responsive' for responsiveness
    table_html = f'<div class="table-responsive"><table class="table table-striped table-bordered text-center">{filtered_data.to_html(classes="table text-center table-bordered", index=False, border=0)}</table></div>'
    
    # Correctly place the download button on the left and the revoke button on the right
    buttons_html = f'''
    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
        <div>
            <form action="/download/{os.path.basename(processed_filename)}" method="get">
                <button type="submit" class="btn btn-primary">Download Processed File</button>
            </form>
        </div>
        <div>
            <form action="/revoke/{os.path.basename(processed_filename)}" method="post">
                <button type="submit" class="btn btn-danger">Revoke Processed Users </button>
            </form>
        </div>
    </div>
    '''
    
    # Combine table and buttons HTML
    combined_html = table_html + buttons_html
    
    return processed_filename, combined_html  # Return both the filename and HTML string

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')



if __name__ == '__main__':
    app.run(debug=True)