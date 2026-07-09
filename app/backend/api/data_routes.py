# data-wrangler/app/backend/api/data_routes.py

import os
import io
import pandas as pd
from flask import request, jsonify, current_app, send_file
from . import api_blueprint
# --- FIX: Use a relative import to find the utils package ---
from ..utils.formatting_utils import format_phone_numbers_in_cell
from . import api_blueprint, socketio

# Define the directory for temporary file uploads, relative to this file's location.
TEMP_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_uploads')

# --- Helper Functions ---

def load_dataframe_from_file(file_path):
    """
    Loads data from a specified file path into a pandas DataFrame.
    Supports various file formats like CSV, TSV, Excel, JSON, and Parquet.
    """
    _, extension = os.path.splitext(file_path)
    ext = extension.lower()
    try:
        if ext == '.csv':
            return pd.read_csv(file_path)
        elif ext == '.tsv':
            return pd.read_csv(file_path, sep='\t')
        elif ext in ['.xls', '.xlsx']:
            return pd.read_excel(file_path, engine='openpyxl')
        elif ext == '.json':
            return pd.read_json(file_path, lines=True)
        elif ext == '.parquet':
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        raise ValueError(f"Error reading file {os.path.basename(file_path)}: {e}")

def cleanup_temp_files(directory, file_identifier, total_chunks):
    """
    Removes temporary chunk files after they have been reassembled.
    """
    try:
        for i in range(total_chunks):
            chunk_path = os.path.join(directory, f"{file_identifier}_chunk_{i}")
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
    except Exception as e:
        print(f"Error during file chunk cleanup: {e}")

# --- API Endpoints ---

@api_blueprint.route('/upload', methods=['POST'])
def upload_chunked_file():
    """
    Handles chunked file uploads, reassembles, and loads the data.
    """
    try:
        file_chunk = request.files.get('file_chunk')
        upload_id = request.form.get('upload_id')
        chunk_index_str = request.form.get('chunk_index')
        total_chunks_str = request.form.get('total_chunks')
        original_filename = request.form.get('original_filename')

        if not all([file_chunk, upload_id, original_filename, chunk_index_str, total_chunks_str]):
            return jsonify({"status": "error", "message": "Missing required upload data"}), 400

        chunk_index = int(chunk_index_str)
        total_chunks = int(total_chunks_str)

        os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
        chunk_path = os.path.join(TEMP_UPLOADS_DIR, f"{upload_id}_chunk_{chunk_index}")
        file_chunk.save(chunk_path)

        if chunk_index == total_chunks - 1:
            reassembled_path = os.path.join(TEMP_UPLOADS_DIR, original_filename)
            try:
                with open(reassembled_path, 'wb') as final_file:
                    for i in range(total_chunks):
                        part_path = os.path.join(TEMP_UPLOADS_DIR, f"{upload_id}_chunk_{i}")
                        with open(part_path, 'rb') as part_file:
                            final_file.write(part_file.read())
                
                df = load_dataframe_from_file(reassembled_path)
                current_app.config['MAIN_DF'] = df
                current_app.config['FILENAME'] = original_filename
                current_app.config['UPLOAD_ID'] = upload_id

                return jsonify({
                    "status": "complete", "message": "File uploaded successfully.",
                    "filename": original_filename, "rows": len(df), "columns": len(df.columns)
                }), 200
            finally:
                cleanup_temp_files(TEMP_UPLOADS_DIR, upload_id, total_chunks)
                if os.path.exists(reassembled_path):
                    os.remove(reassembled_path)
        else:
            return jsonify({"status": "chunk_received", "chunk": chunk_index}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred during upload: {e}"}), 500

@api_blueprint.route('/data', methods=['GET'])
def get_data_preview():
    """
    Provides a paginated, filterable, and sortable view of the current DataFrame.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    page, limit = int(request.args.get('page', 1)), int(request.args.get('limit', 50))
    sort_by, sort_order = request.args.get('sort_by'), request.args.get('sort_order', 'asc')
    global_filter = request.args.get('filter_val')
    df_view = df.copy()

    if global_filter:
        mask = df_view.apply(lambda x: x.astype(str).str.contains(global_filter, case=False, na=False)).any(axis=1)
        df_view = df_view[mask]
    total_records = len(df_view)

    if sort_by in df_view.columns:
        df_view = df_view.sort_values(by=sort_by, ascending=(sort_order == 'asc'), kind='mergesort')

    start_index, end_index = (page - 1) * limit, page * limit
    paginated_df = df_view.iloc[start_index:end_index]

    # Apply formatting for the preview
    for col_name in paginated_df.columns:
        if 'phone' in col_name.lower():
            # Check if it's a string/object type before applying string methods
            if pd.api.types.is_object_dtype(paginated_df[col_name]):
                paginated_df[col_name] = paginated_df[col_name].apply(format_phone_numbers_in_cell)

    response_data = paginated_df.reset_index().rename(columns={'index': 'original_index'})
    response_json = response_data.to_json(orient='records', date_format='iso')
    return jsonify({"status": "success", "data": response_json, "total_records": total_records, "page": page, "limit": limit})

@api_blueprint.route('/edit-cell', methods=['POST'])
def edit_cell():
    """
    Edits a single cell in the main DataFrame using its original index.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None: return jsonify({"status": "error", "message": "No data loaded."}), 404
    data = request.get_json()
    row_index, column_name, new_value = data.get('original_index'), data.get('column_name'), data.get('new_value')
    if row_index is None or column_name is None:
        return jsonify({"status": "error", "message": "Missing required data."}), 400
    try:
        current_app.config['MAIN_DF'].at[row_index, column_name] = new_value
        return jsonify({"status": "success", "message": f"Cell updated."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not update cell: {e}"}), 500

@api_blueprint.route('/export', methods=['POST'])
def export_data():
    """
    Exports the current DataFrame to a file, applying the same formatting as the preview.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data to export."}), 404

    data = request.get_json()
    export_format = data.get('format', 'csv')
    filename = data.get('filename', f'export.{export_format}')

    if not filename.endswith(f'.{export_format}'):
        filename = f'{os.path.splitext(filename)[0]}.{export_format}'

    # Create a copy to avoid modifying the main DataFrame in memory
    df_to_export = df.copy()

    # Apply phone number formatting to all relevant columns in the copied DataFrame
    for col_name in df_to_export.columns:
        if 'phone' in col_name.lower():
             # Check if it's a string/object type to avoid errors on numeric columns
            if pd.api.types.is_object_dtype(df_to_export[col_name]):
                df_to_export[col_name] = df_to_export[col_name].apply(format_phone_numbers_in_cell)

    buffer = io.BytesIO()
    try:
        # Use the formatted DataFrame 'df_to_export' for file generation
        if export_format == 'csv':
            df_to_export.to_csv(buffer, index=False, encoding='utf-8')
            mimetype = 'text/csv'
        elif export_format == 'xlsx':
            df_to_export.to_excel(buffer, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif export_format == 'json':
            df_to_export.to_json(buffer, orient='records', indent=2, date_format='iso')
            mimetype = 'application/json'
        elif export_format == 'parquet':
            df_to_export.to_parquet(buffer, index=False)
            mimetype = 'application/octet-stream'
        else:
            return jsonify({"status": "error", "message": "Unsupported format."}), 400

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error exporting data: {str(e)}"}), 500