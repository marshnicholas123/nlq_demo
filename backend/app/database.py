import mysql.connector
import sqlite3
import os
from app.config import settings

def get_db_connection():
    """Create database connection - MySQL with SQLite fallback"""
    # Check if SQLite database exists for testing/development
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nuclear_plants.db")

    if os.path.exists(sqlite_path):
        # Use SQLite for local development/testing
        return sqlite3.connect(sqlite_path)
    else:
        # Use MySQL for production
        return mysql.connector.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            database=settings.mysql_database,
            user=settings.mysql_user,
            password=settings.mysql_password
        )