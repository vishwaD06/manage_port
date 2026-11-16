import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(use_database=True):
    """
    Establish and return a connection to MySQL/MariaDB.
    If use_database is False, connects to the MySQL server without selecting a DB
    (useful during database creation / initialization).
    """
    kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "autocommit": False,
        "use_pure": True
    }
    if use_database:
        kwargs["database"] = Config.DB_NAME

    try:
        connection = mysql.connector.connect(**kwargs)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise e

def execute_query(sql, params=None, fetch=None, commit=False):
    """
    Execute a parameterized SQL query with proper resource cleanup.
    
    :param sql: SQL statement string
    :param params: tuple or list of parameters
    :param fetch: 'all', 'one', or None
    :param commit: True for INSERT, UPDATE, DELETE
    :return: query results, lastrowid, or affected rowcount
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        
        result = None
        if fetch == 'all':
            result = cursor.fetchall()
        elif fetch == 'one':
            result = cursor.fetchone()
        
        if commit:
            conn.commit()
            # If it was an INSERT, return the new auto-increment ID if generated
            if cursor.lastrowid:
                result = cursor.lastrowid
            else:
                result = cursor.rowcount
                
        return result
    except Error as e:
        if conn and commit:
            conn.rollback()
        logger.error(f"Query execution error: {e} | SQL: {sql} | Params: {params}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def call_procedure(proc_name, args, commit=True):
    """
    Call a MySQL Stored Procedure safely.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(proc_name, args)
        if commit:
            conn.commit()
        return True
    except Error as e:
        if conn and commit:
            conn.rollback()
        logger.error(f"Stored procedure error in {proc_name}: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def execute_script_file(filepath, connection):
    """
    Execute a multi-statement SQL script file supporting DELIMITER syntax.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        script = f.read()

    cursor = connection.cursor()
    # Simple delimiter-aware parser for triggers and procedures
    current_delimiter = ';'
    statements = []
    current_stmt = []

    lines = script.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith('DELIMITER'):
            parts = stripped.split()
            if len(parts) >= 2:
                current_delimiter = parts[1]
            continue

        # Skip SQL comments and empty lines
        if stripped.startswith('--') or stripped.startswith('#') or stripped.startswith('/*') or stripped.endswith('*/'):
            continue
        if not stripped:
            continue

        if current_delimiter != ';':
            if stripped.endswith(current_delimiter):
                # Cut the delimiter off
                clean_line = line[:line.rfind(current_delimiter)]
                current_stmt.append(clean_line)
                full_stmt = "\n".join(current_stmt).strip()
                if full_stmt:
                    statements.append(full_stmt)
                current_stmt = []
            else:
                current_stmt.append(line)
        else:
            if stripped.endswith(';'):
                clean_line = line[:line.rfind(';')]
                current_stmt.append(clean_line)
                full_stmt = "\n".join(current_stmt).strip()
                if full_stmt:
                    statements.append(full_stmt)
                current_stmt = []
            else:
                current_stmt.append(line)

    for stmt in statements:
        stmt_clean = stmt.strip()
        if stmt_clean:
            try:
                cursor.execute(stmt_clean)
            except Error as err:
                # Log but continue or re-raise
                logger.warning(f"Notice on statement: {err}\nStmt: {stmt_clean[:100]}...")
    connection.commit()
    cursor.close()

def init_database():
    """
    Runs schema.sql and seed.sql to establish the database from scratch.
    """
    logger.info("Connecting to MySQL server to initialize database...")
    conn = get_db_connection(use_database=False)
    
    logger.info("Executing schema.sql...")
    execute_script_file("schema.sql", conn)
    
    logger.info("Executing seed.sql...")
    execute_script_file("seed.sql", conn)
    
    conn.close()
    logger.info("Database initialized and seeded successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_database()
    else:
        print("Checking database connection...")
        try:
            conn = get_db_connection()
            if conn.is_connected():
                print(f"Connected successfully to MySQL database '{Config.DB_NAME}' on {Config.DB_HOST}:{Config.DB_PORT}")
                conn.close()
        except Exception as ex:
            print(f"Connection check failed: {ex}")
