import gradio as gr
from upload import save_file
from list_files import get_uploaded_files
from embedd_model import execute_sql, generate_sql, model_options, language_options, get_files
from rag_application import search_and_generate
from view_vectors import get_vector_data
from maintenance import delete_table_data

files = get_files()

with gr.Blocks() as demo:
    with gr.Tab("1.ファイルアップロード[upload.py]"):
        gr.Markdown("## ファイルをアップロードし、Oracle DBに挿入")
        upload_output = gr.Textbox(label="アップロード結果")
        upload_file = gr.File(label="ファイルを選択", type="filepath")
        upload_button = gr.Button("アップロード")
        upload_button.click(save_file, inputs=upload_file, outputs=upload_output)

    with gr.Tab("2.ファイル一覧[list_files.py]"):
        gr.Markdown("## アップロードされたファイル一覧")
        table_output = gr.DataFrame(label="ファイル一覧")
        display_button = gr.Button("ファイル一覧を表示")
        display_button.click(get_uploaded_files, outputs=table_output)

    with gr.Tab("3.ベクトル化処理[embedd_model.py]"):
        gr.Markdown("## Embeddモデルとファイル選択")
        model_dropdown = gr.Dropdown(label="Embeddモデルを選択してください", choices=list(model_options.keys()))
        file_dropdown = gr.Dropdown(label="対象ファイルを選択してください", choices=list(files.keys()))
        language_dropdown = gr.Dropdown(label="言語設定を選択してください", choices=list(language_options.keys()))
        chunk_size_slider = gr.Slider(label="チャンクサイズ", minimum=0, maximum=500, step=10, value=200)
        overlap_slider = gr.Slider(label="オーバーラップ(%)", minimum=0, maximum=100, step=5, value=0)
        output = gr.Textbox(label="実行結果")
        submit_button = gr.Button("実行")
        submit_button.click(lambda model, file, language, chunk_size, overlap: execute_sql(generate_sql(files[file], chunk_size, overlap, language_options[language])),
                            inputs=[model_dropdown, file_dropdown, language_dropdown, chunk_size_slider, overlap_slider],
                            outputs=output)

    with gr.TabItem("4.ベクトル化確認[view_vectors.py]"):
        gr.Markdown("## ベクトル化データを確認")
        vector_output = gr.DataFrame(label="ベクトル化データ")
        view_button = gr.Button("ベクトル化データを表示")
        view_button.click(get_vector_data, outputs=vector_output)

    with gr.Tab("5.ベクトル検索[rag_application.py]"):
        gr.Markdown("# RAGアプリケーション\n入力されたテキストをOracle DBで検索し、検索結果からLLMで回答を生成します。")
        with gr.Row():
            input_text = gr.Textbox(lines=2, placeholder="検索するテキストを入力してください...", label="検索テキスト")
        with gr.Row():
            max_tokens = gr.Slider(minimum=1, maximum=1000, step=1, value=600, label="max_tokens")
            temperature = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=1.0, label="temperature")
            frequency_penalty = gr.Slider(minimum=0.0, maximum=2.0, step=0.01, value=0.0, label="frequency_penalty")
            top_p = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=0.75, label="top_p")
            top_k = gr.Slider(minimum=0, maximum=100, step=1, value=0, label="top_k")
        with gr.Row():
            output_table = gr.Dataframe(label="OracleDB23aiに対するベクトル検索結果")
        with gr.Row():
            output_text = gr.Textbox(label="生成された応答")
        submit_button = gr.Button("検索実行")

        submit_button.click(search_and_generate, inputs=[input_text, max_tokens, temperature, frequency_penalty, top_p, top_k], outputs=[output_table, output_text])
    
    with gr.Tab("99.メンテナンス[maintenance.py]"):
        gr.Markdown("## データベースのメンテナンス")
        table_dropdown = gr.Dropdown(label="テーブルを選択してください", choices=["app_doc_tab", "app_chunk_tab"])
        maintenance_output = gr.Textbox(label="メンテナンス結果")
        delete_button = gr.Button("削除")
        delete_button.click(delete_table_data, inputs=table_dropdown, outputs=maintenance_output)

demo.launch()

