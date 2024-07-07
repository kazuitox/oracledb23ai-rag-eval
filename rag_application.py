import os
import oracledb
import pandas as pd
import oci
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DSN = os.getenv('DB_DSN')
oci_config_profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
oci_compartment_id = os.getenv("OCI_COMPARTMENT_ID")

def search_and_generate(input_text, max_tokens, temperature, frequency_penalty, top_p, top_k):
    try:
        connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = connection.cursor()

        embed_genai_params = '{"provider": "ocigenai", "credential_name": "OCI_CRED", "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText", "model": "cohere.embed-multilingual-v3.0"}'

        plsql_block = """
        BEGIN
            :embed_genai_params := '{"provider": "ocigenai", "credential_name": "OCI_CRED", "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText", "model": "cohere.embed-multilingual-v3.0"}';
        END;
        """

        cursor.execute(plsql_block, {'embed_genai_params': embed_genai_params})

        sql_query = f"""
        SELECT doc_id, embed_id, REPLACE(REPLACE(EMBED_DATA, CHR(10), ''), CHR(13), '') AS EMBED_DATA
        FROM app_chunk_tab
        ORDER BY vector_distance(embed_vector_genai , (SELECT to_vector(et.embed_vector_genai) embed_vector_genai
        FROM
        dbms_vector_chain.utl_to_embeddings(:input_text, JSON(:embed_genai_params)) t,
        JSON_TABLE ( t.column_value, '$[*]'
        COLUMNS (
        embed_id NUMBER PATH '$.embed_id', embed_data VARCHAR2 ( 4000 ) PATH '$.embed_data', embed_vector_genai CLOB PATH '$.embed_vector_genai'
        ))et), COSINE)
        FETCH FIRST 10 ROWS ONLY
        """

        cursor.execute(sql_query, {'input_text': input_text, 'embed_genai_params': embed_genai_params})
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        df = pd.DataFrame(results, columns=['doc_id', 'embed_id', 'EMBED_DATA'])

        search_results_text = "\n".join(df['EMBED_DATA'])
        config = oci.config.from_file('~/.oci/config', oci_config_profile)
        endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
        generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240)
        )
        chat_detail = oci.generative_ai_inference.models.ChatDetails()

        chat_request = oci.generative_ai_inference.models.CohereChatRequest()
        chat_request.message = f"{input_text}について、以下の検索結果に基づいて応答を生成してください:\n{search_results_text}"
        chat_request.max_tokens = max_tokens
        chat_request.temperature = temperature
        chat_request.frequency_penalty = frequency_penalty
        chat_request.top_p = top_p
        chat_request.top_k = top_k

        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
            model_id="ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceya7ozidbukxwtun4ocm4ngco2jukoaht5mygpgr6gq2lgq"
        )
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = oci_compartment_id
        chat_response = generative_ai_inference_client.chat(chat_detail)

        response_content = chat_response.data.chat_response.text.strip()

        return df, response_content
    except oracledb.DatabaseError as e:
        return pd.DataFrame(), "データベース接続エラー: " + str(e)
    except AttributeError as e:
        return pd.DataFrame(), "AttributeError: " + str(e)

