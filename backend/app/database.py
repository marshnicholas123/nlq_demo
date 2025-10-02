import mysql.connector
from app.config import settings

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password
    )