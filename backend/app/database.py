import mysql.connector
import sqlite3
import os
from app.config import settings

def get_db_connection():
    """Create database connection - MySQL with SQLite fallback"""
    # Check if SQLite database exists for testing/development
    # __file__ is backend/app/database.py
    # Go up 3 levels to reach text2sql_ui directory
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nuclear_plants.db")

    # Also check the current working directory
    cwd_sqlite_path = os.path.join(os.getcwd(), "nuclear_plants.db")

    # Prefer SQLite if it exists in either location
    if os.path.exists(sqlite_path):
        print(f"Using SQLite database at: {sqlite_path}")
        return sqlite3.connect(sqlite_path)
    elif os.path.exists(cwd_sqlite_path):
        print(f"Using SQLite database at: {cwd_sqlite_path}")
        return sqlite3.connect(cwd_sqlite_path)
    else:
        # Use MySQL for production
        print(f"SQLite not found at {sqlite_path} or {cwd_sqlite_path}, attempting MySQL connection")
        return mysql.connector.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            database=settings.mysql_database,
            user=settings.mysql_user,
            password=settings.mysql_password
        )