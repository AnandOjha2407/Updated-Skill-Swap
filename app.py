from flask import Flask,jsonify, render_template, request, redirect, url_for
from pymongo import MongoClient
import bcrypt
from gridfs import GridFS
from dotenv import load_dotenv
import io
import os
import datetime
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["skill_swap_db"]
users_collection = db["users"]
# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client['skill_swap_db']  # Correct database name
users_collection = db['users']  # Correct collection name
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
    query = request.args.get('query', '').strip()

    if not query:
        return render_template('landing.html', users=None)  # No results when search is empty

    # MongoDB query using regex for case-insensitive search
    filtered_users = list(users_collection.find({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},  
            {"skills": {"$regex": query, "$options": "i"}},
            {"purpose": {"$regex": query, "$options": "i"}}
        ]
    }))

    return render_template('landing.html', users=filtered_users) 




## MongoDB Connection
db = client["skill_swap_db"]
projects_collection = db["projects"]  # Projects schema
fs = GridFS(db)  # For file storage

@app.route("/collaboration", methods=["POST"])
def create_repository():
    try:
        # Get form data
        repo_name = request.form.get("name")
        description = request.form.get("description")
        uploaded_files = request.files.getlist("files")

        # Store file references
        file_ids = []
        for file in uploaded_files:
            if file.filename:
                file_id = fs.put(file, filename=file.filename)
                file_ids.append(file_id)

        # Store project details in MongoDB
        project_data = {
            "repo_name": repo_name,
            "description": description,
            "file_ids": file_ids,
            "created_at": datetime.datetime.utcnow()
        }
        projects_collection.insert_one(project_data)

        return jsonify({"message": "Repository created successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_repositories", methods=["GET"])
def get_repositories():
    try:
        projects = projects_collection.find({})
        repo_list = []

        for project in projects:
            file_details = []
            
            if "file_ids" in project:
                for file_id in project["file_ids"]:
                    file_obj = fs.get(file_id)
                    file_details.append({
                        "file_id": str(file_id),
                        "filename": file_obj.filename
                    })

            repo_list.append({
                "name": project.get("repo_name", "Untitled"),
                "description": project.get("description", "No description"),
                "file_types": [file["filename"].split(".")[-1] for file in file_details],  # Extract file extensions
                "files": file_details
            })

        return jsonify(repo_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/download/<file_id>", methods=["GET"])
def download_file(file_id):
    try:
        # Fetch file from GridFS
        file_obj = fs.get(ObjectId(file_id))

        # Stream file content to the client
        return send_file(
            io.BytesIO(file_obj.read()),  # Convert file to stream
            mimetype="application/octet-stream",  # Generic binary type
            as_attachment=True,
            download_name=file_obj.filename  # Use original filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
