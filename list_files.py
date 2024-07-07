import os
import oracledb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')

def get_uploaded_files():
    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        sql = "SELECT id, filename FROM app_doc_tab ORDER BY id ASC"
        cursor.execute(sql)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        return df
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

