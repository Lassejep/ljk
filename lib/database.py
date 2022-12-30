import sqlite3
import os

def create_database(database_name):
    """Create a database with the given name."""
    # Create the database
    conn = sqlite3.connect(database_name)
    database_cursor = conn.cursor()
    return conn, database_cursor

def delete_database(database_name):
    """Delete the database with the given name."""
    # Delete the database
    os.remove(database_name)

def create_table(database_cursor, table_name, columns):
    """Create a table with the given name and columns."""
    # Create the table
    database_cursor.execute("CREATE TABLE %s (%s)" % (table_name, columns))

