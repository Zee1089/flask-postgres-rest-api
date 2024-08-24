from flask import Flask, request
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras


load_dotenv()

#  Initialize Flask, We'll use the pre-defined global '__name__' variable to tell Flask where it is.
app = Flask(__name__)


# app.py
def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='researchpapers_db',
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD']
    )
    return connection


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



# Run our application, by default on port 5000
if __name__ == '__main__':
    app.run(port=5003)