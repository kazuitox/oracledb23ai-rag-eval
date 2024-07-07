import os
import oracledb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')

model_options = {
    "GenAI(Cohere)": "cohere.embed-multilingual-v3.0",
    "OpenAI": "text-embedding-3-large"
}

language_options = {
    "日本語": "JAPANESE",
    "英語": "ENGLISH"
}

def get_files():
    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        sql = "SELECT id, filename FROM app_doc_tab ORDER BY id ASC"
        cursor.execute(sql)
        result = cursor.fetchall()
        files = {row[1]: row[0] for row in result}
        return files
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

files = get_files()

def generate_sql(file_id, chunk_size, overlap, language):
    json_params = '{"max": "' + str(chunk_size) + '", "overlap": "' + str(overlap) + '%", "language": "' + language + '"}'
    embed_params = '{"provider": "ocigenai", "credential_name": "OCI_CRED", "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText", "model": "cohere.embed-multilingual-v3.0"}'

    sql = f"""
    insert into app_chunk_tab (doc_id, embed_id, embed_data, embed_vector_genai)
    with t_chunk as (
      select dt.id as doc_id, et.chunk_id as embed_id, et.chunk_data as embed_data
      from
        app_doc_tab dt,
        table(dbms_vector_chain.utl_to_chunks(
          dbms_vector_chain.utl_to_text(dt.data), json('{json_params}')
        )) t,
        JSON_TABLE(t.column_value, '$[*]'
          COLUMNS (chunk_id NUMBER PATH '$.chunk_id', chunk_data VARCHAR2(4000) PATH '$.chunk_data')
        ) et
      where dt.id = {file_id}
    ),
    t_embed as (
      select dt.id as doc_id, rownum as embed_id, to_vector(t.column_value) as embed_vector
      from
        app_doc_tab dt,
        table(dbms_vector_chain.utl_to_embeddings(
          dbms_vector_chain.utl_to_chunks(
            dbms_vector_chain.utl_to_text(dt.data), json('{json_params}')
          ),
          json('{embed_params}')
        )) t
      where dt.id = {file_id}
    )
    select t_chunk.doc_id, t_chunk.embed_id, t_chunk.embed_data, t_embed.embed_vector as embed_vector_genai
    from t_chunk
    join t_embed on t_chunk.doc_id = t_embed.doc_id and t_chunk.embed_id = t_embed.embed_id
    """
    return sql

def execute_sql(sql):
    connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        connection.commit()
        return "SQL executed successfully."
    except oracledb.DatabaseError as e:
        error, = e.args
        return f"Database error occurred: {error.message}"
    finally:
        cursor.close()
        connection.close()

