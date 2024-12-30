from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import bcrypt
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploaded_files'  # Directory for storing files

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="anand",  # Replace with your MySQL username
    password="anandkhushi@2407",  # Replace with your MySQL password
    database="skill_swap_db"  # Database name
)
cursor = db.cursor(dictionary=True)

# Route for the form page
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['name']
        skills = request.form['skills']
        purpose = request.form['purpose']
        contact = request.form['contact']
        profile_picture = request.form['profile_picture']
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists in MySQL
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            error_message = "Email already registered!"
            return render_template('form.html', error=error_message)

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Add user to MySQL
        cursor.execute(
            "INSERT INTO users (name, skills, purpose, contact, profile_picture, email, password) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, skills, purpose, contact, profile_picture, email, hashed_password)
        )
        db.commit()

        return redirect('/landing')  # Redirect to the landing page
    return render_template('form.html')


@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        files = request.files.getlist('files')

        # Save uploaded files
        file_paths = []
        for file in files:
            if file.filename:  # Check if the file is not empty
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                file_paths.append(file.filename)

        # Store data in the MySQL database
        cursor.execute(
            "INSERT INTO projects (name, description, files) VALUES (%s, %s, %s)",
            (name, description, ','.join(file_paths))
        )
        db.commit()

        return redirect(url_for('view_projects'))
    return render_template('create_project.html')


@app.route('/view_projects', methods=['GET'])
def view_projects():
    # Fetch all projects from MySQL
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    return render_template('view_projects.html', projects=projects)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None  # Variable to hold error message
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch the user from MySQL
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Login successful
            return redirect('/landing')
        else:
            error_message = "Login failed, check your email or password. Retry"

    return render_template('login.html', error_message=error_message)


@app.route('/landing', methods=['GET'])
def landing():
    query = request.args.get('query', '').strip().lower()
    filter_selected = request.args.getlist('filter')  # Get selected filters

    # Fetch users from MySQL
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Filter users based on the query
    filtered_users = [
        user for user in users
        if query in user['name'].lower() or
           query in user['skills'].lower() or
           query in user['purpose'].lower()
    ]

    # Apply additional filters if any are selected
    if filter_selected:
        for filter_item in filter_selected:
            if filter_item == 'hackathon':
                filtered_users = [user for user in filtered_users if 'hackathon' in user['skills'].lower()]
            elif filter_item == 'project':
                filtered_users = [user for user in filtered_users if 'project' in user['skills'].lower()]
            elif filter_item == 'skill_up':
                filtered_users = [user for user in filtered_users if 'skill up' in user['skills'].lower()]
            elif filter_item == 'web_development':
                filtered_users = [user for user in filtered_users if 'web development' in user['skills'].lower()]
            elif filter_item == 'aiml':
                filtered_users = [
                    user for user in filtered_users
                    if 'aiml' in user['skills'].lower() or
                       'artificial intelligence' in user['skills'].lower() or
                       'machine learning' in user['skills'].lower()
                ]

    return render_template('landing.html', users=filtered_users)


@app.route('/collaborate', methods=['GET'])
def collaborate():
    return render_template('collaborate.html')


@app.route('/code_board', methods=['GET'])
def code_board():
    return render_template('code_board.html')


@app.route('/skill_swap', methods=['GET'])
def skill_swap():
    return render_template('skill_swap.html')


@app.route('/users')
def users_page():
    # Fetch users from MySQL
    cursor.execute("SELECT name, skills, purpose, contact, profile_picture, email FROM users")
    users = cursor.fetchall()
    return render_template('users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
