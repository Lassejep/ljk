import os
import sqlite3

# Get the directory in which the script is located
script_dir = os.path.dirname(__file__)

# Create the path to the database file
db_path = os.path.join(script_dir, "/db/users.db")

# Connect to the database
conn = sqlite3.connect(db_path)

# Create a cursor
cursor = conn.cursor()

# Create the table
cursor.execute(
    "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)"
)

# Commit the changes
conn.commit()

# Close the connection
conn.close()