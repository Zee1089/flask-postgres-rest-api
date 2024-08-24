from flask import Flask, request, jsonify, g
from flask_cors import CORS
from auth_middleware import token_required
import jwt
import bcrypt
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

load_dotenv()

#  Initialize Flask, We'll use the pre-defined global '__name__' variable to tell Flask where it is.
app = Flask(__name__)
CORS(app)

def get_db_connection_auth():
    connection = psycopg2.connect(
        host='localhost',
        database='flask_auth_db',
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD'))
    return connection


# app.py
def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='researchpapers_db',
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD']
    )
    return connection

# app.py
@app.route('/sign-token')
def sign_token():
    user = {
        "id": 1,
        "username": "test",
        "password": "test"
    }
    token = jwt.encode(user, os.getenv('JWT_SECRET'), algorithm="HS256")
    # return token
    return jsonify({"token": token})

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        decoded_token = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
        return jsonify({"user": decoded_token})
    except Exception as error:
       return jsonify({"error": error.message})

@app.route('/vip-lounge')
@token_required
def vip_lounge():
    return f"Welcome to the party, {g.user['username']}"
    

@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        new_user_data = request.get_json()
        connection = get_db_connection_auth()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT * FROM users WHERE username = %s;", (new_user_data["username"],))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            return jsonify({"error": "Username already taken"}), 400

        hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING username", (new_user_data["username"], hashed_password.decode('utf-8')))
        created_user = cursor.fetchone()
        connection.commit()
        connection.close()
        token = jwt.encode(created_user, os.getenv('JWT_SECRET'))
        return jsonify({"token": token, "user": created_user}), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 401

@app.route('/auth/signin', methods=["POST"])
def signin():
    try:
        sign_in_form_data = request.get_json()
        connection = get_db_connection_auth()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s;", (sign_in_form_data["username"],))
        existing_user = cursor.fetchone()

        if existing_user is None:
            return jsonify({"error": "Invalid credentials."}), 401

        password_is_valid = bcrypt.checkpw(bytes(sign_in_form_data["password"], 'utf-8'), bytes(existing_user["password"], 'utf-8'))

        if not password_is_valid:
            return jsonify({"error": "Invdddalid credentials."}), 401

        # Updated code:
        token = jwt.encode({"username": existing_user["username"], "id": existing_user["id"]}, os.getenv('JWT_SECRET'))
        return jsonify({"token": token}), 201


    except Exception as error:
        return jsonify({"error": "Invalid credentials."}), 401
    finally:
        connection.close()



# Define our route, This syntax is using a Python decorator, which is essentially a succinct way to wrap a function in another function.
@app.route('/')
def ind():
  return "Hello, world!"


# app.py
@app.route('/researchpapers')
def researchpapers_index():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM researchpapers;")
        researchpapers = cursor.fetchall()
        connection.close()
        return researchpapers
    except:
        return "Application Error", 500

@app.route('/researchpapers', methods=['POST'])
def create_researchpaper():
    try:
        new_researchpaper = request.json  # Get the incoming JSON data
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Insert into researchpapers without the URL field
        cursor.execute(
            "INSERT INTO researchpapers (title, authors, journal, publication_date, major_findings) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (
                new_researchpaper['title'],
                new_researchpaper['authors'],
                new_researchpaper['journal'],
                new_researchpaper['publication_date'],
                new_researchpaper['major_findings']
            )
        )
        
        created_researchpaper = cursor.fetchone()
        connection.commit()  # Commit the transaction
        cursor.close()
        connection.close()
        
        return created_researchpaper, 201  # Return the created record with status 201
    except Exception as e:
        return str(e), 500  # Return the error message with status 500 if something goes wrong


# Show route

@app.route('/researchpapers/<researchpaper_id>', methods=['GET'])
def show_researchpaper(researchpaper_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM researchpapers WHERE id = %s", (researchpaper_id))
        researchpaper = cursor.fetchone()
        if researchpaper is None:
            connection.close()
            return "Research Article Not Found", 404
        connection.close()
        return researchpaper, 200
    except Exception as e:
        return str(e),500


@app.route('/researchpapers/<researchpaper_id>', methods=['DELETE'])
def delete_researchpaper(researchpaper_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("DELETE FROM researchpapers WHERE id = %s", (researchpaper_id,))
        connection.commit()  # Commit the deletion
        cursor.close()
        connection.close()
        return "Research Article deleted successfully", 204
    except Exception as e:
        return str(e), 500

@app.route('/researchpapers/<researchpaper_id>', methods=['PUT'])
def update_researchpaper(researchpaper_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "UPDATE researchpapers SET title = %s, authors = %s, journal = %s, publication_date = %s, major_findings = %s WHERE id = %s RETURNING *", 
            (
                request.json['title'], 
                request.json['authors'], 
                request.json['journal'],
                request.json['publication_date'],
                request.json['major_findings'],
                researchpaper_id
            )
        )

        updated_researchpaper = cursor.fetchone()
        if updated_researchpaper is None:
            return "Research Article Not Found", 404
        connection.commit()
        connection.close()
        return updated_researchpaper, 202
    except Exception as e:
        return str(e), 500



# Run our application, by default on port 5000
if __name__ == '__main__':
    app.run(port=5003)