import os
import shutil
import oracledb
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')

def save_file(file_path):
    filename = os.path.basename(file_path)
    save_dir = "/home/oracle/data/files"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, filename)
    shutil.copy(file_path, save_path)

    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO app_doc_tab (filename, data) VALUES (:filename, to_blob(bfilename('FILE_DIR', :filename)))"
        cursor.execute(sql, {'filename': filename})
        connection.commit()
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

    return f"File saved to {save_path} and inserted into Oracle DB"

