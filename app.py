from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import bcrypt
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploaded_files'  # Directory for storing files

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB Atlas connection
client = MongoClient('mongodb+srv://Anand_Ojha:anandojha2407@skillswapdb.k5rzx.mongodb.net/')
db = client.skill_swap_db  # Database name
users_collection = db.users  # Collection for storing user data
projects_collection = db.projects  # Collection for storing project data

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

        # Check if the email already exists in MongoDB
        if users_collection.find_one({"email": email}):
            error_message = "Email already registered!"
            return render_template('form.html', error=error_message)

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Add user to MongoDB
        users_collection.insert_one({
            "name": name,
            "skills": skills,
            "purpose": purpose,
            "contact": contact,
            "profile_picture": profile_picture,
            "email": email,
            "password": hashed_password
        })

        return redirect('/landing')  # Redirect to the landing page
    return render_template('form.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()  # Get the search query from URL parameters

    # Fetch users from MongoDB
    users = list(users_collection.find())  # Fetch all users

    # Filter users based on the search query
    filtered_users = [
        user for user in users
        if query in user['name'].lower() or
           query in user['skills'].lower() or
           query in user['purpose'].lower()
    ]

    return render_template('landing.html', users=filtered_users)  # Pass filtered users to the template

# Create Project Route
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

        # Store project data in MongoDB
        projects_collection.insert_one({
            "name": name,
            "description": description,
            "files": file_paths
        })

        return redirect(url_for('view_projects'))
    return render_template('create_project.html')

# View Projects Route
@app.route('/view_projects', methods=['GET'])
def view_projects():
    # Fetch all projects from MongoDB
    projects = list(projects_collection.find())
    return render_template('view_projects.html', projects=projects)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None  # Variable to hold error message
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch the user from MongoDB
        user = users_collection.find_one({"email": email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')): 
            # Login successful, redirect to the landing page
            return redirect('/landing')
        else:
            error_message = "Login failed, check your email or password. Retry"

    return render_template('login.html', error_message=error_message)

#landing route

@app.route('/landing', methods=['GET'])
def landing():
    query = request.args.get('query', '').strip().lower()  # Get the search query from URL parameters
    filter_selected = request.args.getlist('filter')  # Get selected filters

    users = []  # Initialize an empty list for users

    # Only fetch users if there is a search query
    if query:
        # Fetch users from MongoDB
        users = list(users_collection.find())

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
    else:
        filtered_users = []  # If no query, don't display users

    return render_template('landing.html', users=filtered_users)


# Collaboration Route
@app.route('/collaborate', methods=['GET'])
def collaborate():
    return render_template('collaborate.html')

# Code Board Route
@app.route('/code_board', methods=['GET'])
def code_board():
    return render_template('code_board.html')

# Skill Swap Route
@app.route('/skill_swap', methods=['GET'])
def skill_swap():
    return render_template('skill_swap.html')

# Users Page Route
@app.route('/users')
def users_page():
    # Fetch users from MongoDB
    users = list(users_collection.find({}, {"name": 1, "skills": 1, "purpose": 1, "contact": 1, "profile_picture": 1, "email": 1}))
    return render_template('users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
