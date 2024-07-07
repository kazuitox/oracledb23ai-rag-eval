import os
import oracledb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')

def get_vector_data():
    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        sql = """
        SELECT
            d.ID AS doc_id,
            d.FILENAME,
            REPLACE(REPLACE(c.EMBED_DATA, CHR(10), ''), CHR(13), '') AS EMBED_DATA,
            c.EMBED_VECTOR_GENAI
        FROM
            app_doc_tab d
        JOIN
            app_chunk_tab c
        ON
            d.ID = c.DOC_ID
        ORDER BY
            d.ID ASC
        """
        cursor.execute(sql)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        #df['EMBED_VECTOR_GENAI'] = df['EMBED_VECTOR_GENAI'].apply(lambda x: str(x)[:20] + '...' if len(str(x)) > 20 else x)
        df['EMBED_DATA'] = df['EMBED_DATA'].apply(lambda x: str(x)[:20] + '...' if len(str(x)) > 20 else x)
        #df['EMBED_VECTOR_GENAI'] = df['EMBED_VECTOR_GENAI'].apply(lambda x: str(x)[:20] + '...' if len(str(x)) > 20 else x)
        df['EMBED_VECTOR_GENAI'] = df['EMBED_VECTOR_GENAI'].apply(lambda x: str(x)[10:-1][:20] + '...' if len(str(x)) > 20 else str(x)[10:-1])


        return df
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

