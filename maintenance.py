import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')

def delete_table_data(table_name):
    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        sql = f"DELETE FROM {table_name}"
        cursor.execute(sql)
        connection.commit()
        return f"Data from {table_name} has been deleted successfully."
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

