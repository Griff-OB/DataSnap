# data-wrangler/app/backend/api/cleaning_routes.py

import pandas as pd
import re
from flask import request, jsonify, current_app

from . import api_blueprint, socketio

# --- Email Validation Helper ---
# A reasonably robust regex for email validation.
# It checks for a typical structure: local-part@domain.
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@api_blueprint.route('/clean/handle-missing', methods=['POST'])
def handle_missing_values():
    """
    Handles missing values in the DataFrame based on the provided method.
    Methods: remove rows, fill with mean/median/value, forward/backward fill.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    df_cleaned = df.copy()
    data = request.get_json()
    method = data.get('method', 'remove')
    columns = data.get('columns', [])
    fill_value = data.get('fill_value')

    try:
        target_cols = columns if columns else df_cleaned.columns.tolist()

        if method == 'remove':
            df_cleaned.dropna(subset=target_cols, inplace=True)
        elif method in ['fill_mean', 'fill_median']:
            numeric_cols = df_cleaned.select_dtypes(include=['number']).columns
            cols_to_fill = [col for col in target_cols if col in numeric_cols]
            for col in cols_to_fill:
                fill_val = df_cleaned[col].mean() if method == 'fill_mean' else df_cleaned[col].median()
                df_cleaned[col].fillna(fill_val, inplace=True)
        elif method == 'fill_value':
            if fill_value is not None:
                df_cleaned[target_cols] = df_cleaned[target_cols].fillna(fill_value)
        elif method == 'forward_fill':
            df_cleaned[target_cols] = df_cleaned[target_cols].fillna(method='ffill')
        elif method == 'backward_fill':
            df_cleaned[target_cols] = df_cleaned[target_cols].fillna(method='bfill')
        else:
            return jsonify({"status": "error", "message": "Invalid method specified."}), 400

        current_app.config['MAIN_DF'] = df_cleaned
        return jsonify({"status": "success", "message": f"Missing values handled.", "new_shape": df_cleaned.shape})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error handling missing values: {str(e)}"}), 500


@api_blueprint.route('/clean/remove-duplicates', methods=['POST'])
def remove_duplicates():
    """
    Removes duplicate rows from the DataFrame. Can check all columns or a subset.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    data = request.get_json()
    subset = data.get('columns') if data.get('columns') else None

    try:
        original_shape = df.shape
        df_cleaned = df.drop_duplicates(subset=subset)
        current_app.config['MAIN_DF'] = df_cleaned

        return jsonify({
            "status": "success",
            "message": "Duplicate rows removed.",
            "duplicates_removed": original_shape[0] - df_cleaned.shape[0]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error removing duplicates: {str(e)}"}), 500


@api_blueprint.route('/clean/handle-outliers', methods=['POST'])
def handle_outliers():
    """
    Handles outliers in numeric columns using the IQR method.
    Actions: remove rows, nullify cells, or cap values.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    df_cleaned = df.copy()
    data = request.get_json()
    method = data.get('method', 'remove')
    columns = data.get('columns', [])

    try:
        target_cols = columns if columns else df_cleaned.select_dtypes(include=['number']).columns.tolist()
        outliers_affected = 0
        for col in target_cols:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                Q1 = df_cleaned[col].quantile(0.25)
                Q3 = df_cleaned[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                mask = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
                outliers_affected += mask.sum()
                if method == 'remove':
                    df_cleaned = df_cleaned[~mask]
                elif method == 'nullify':
                    df_cleaned.loc[mask, col] = None
                elif method == 'cap':
                    df_cleaned.loc[df_cleaned[col] < lower_bound, col] = lower_bound
                    df_cleaned.loc[df_cleaned[col] > upper_bound, col] = upper_bound

        current_app.config['MAIN_DF'] = df_cleaned
        return jsonify({"status": "success", "message": f"Outliers handled.", "outliers_affected": int(outliers_affected)})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error handling outliers: {str(e)}"}), 500


@api_blueprint.route('/clean/string-ops', methods=['POST'])
def string_operations():
    """
    Applies common string operations (trim, lowercase, etc.) to text columns.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    df_cleaned = df.copy()
    data = request.get_json()
    operation = data.get('operation')
    columns = data.get('columns', [])

    try:
        target_cols = columns if columns else df_cleaned.select_dtypes(include=['object', 'string']).columns.tolist()
        for col in target_cols:
            # --- FIX ---
            # The original check was too strict. This new check correctly identifies any column
            # that can be treated as a string, including the common 'object' dtype from CSVs.
            if col in df_cleaned.columns and (pd.api.types.is_string_dtype(df_cleaned[col]) or pd.api.types.is_object_dtype(df_cleaned[col])):
                try:
                    # Apply operations safely. This will skip columns that are 'object' type
                    # but do not contain string-like data (e.g., mixed types).
                    if operation == 'trim':
                        df_cleaned[col] = df_cleaned[col].str.strip()
                    elif operation == 'lower':
                        df_cleaned[col] = df_cleaned[col].str.lower()
                    elif operation == 'upper':
                        df_cleaned[col] = df_cleaned[col].str.upper()
                    elif operation == 'title':
                        df_cleaned[col] = df_cleaned[col].str.title()
                except AttributeError:
                    print(f"Skipping string operation on non-string-like object column: {col}")
                    continue

        current_app.config['MAIN_DF'] = df_cleaned
        return jsonify({"status": "success", "message": f"String operation '{operation}' applied."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error performing string operations: {str(e)}"}), 500


@api_blueprint.route('/clean/find-replace', methods=['POST'])
def find_and_replace():
    """
    Performs a find-and-replace operation on text columns.
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    df_cleaned = df.copy()
    data = request.get_json()
    find_value = data.get('find_value')
    replace_value = data.get('replace_value', '')
    columns = data.get('columns', [])
    match_case = data.get('match_case', False)
    use_regex = data.get('use_regex', False)

    if not find_value:
        return jsonify({"status": "error", "message": "'Find' value cannot be empty."}), 400

    try:
        target_cols = columns if columns else df_cleaned.select_dtypes(include=['object', 'string']).columns.tolist()
        for col in target_cols:
            # --- FIX ---
            # Replaced the overly strict 'is_string_dtype' check with one that also includes 'object' dtype.
            if col in df_cleaned.columns and (pd.api.types.is_string_dtype(df_cleaned[col]) or pd.api.types.is_object_dtype(df_cleaned[col])):
                # The .astype(str) call robustly handles NaNs and other non-string types
                # within the column before attempting the replacement.
                df_cleaned[col] = df_cleaned[col].astype(str).str.replace(
                    find_value, replace_value, case=match_case, regex=use_regex
                )

        current_app.config['MAIN_DF'] = df_cleaned
        return jsonify({"status": "success", "message": f"Replaced '{find_value}' with '{replace_value}'."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error during find and replace: {str(e)}"}), 500


@api_blueprint.route('/clean/validate-emails', methods=['POST'])
def validate_emails():
    """
    Validates email formats in specified columns.
    Actions: 'clear' (nullify invalid cells) or 'remove_row' (delete rows with invalid emails).
    """
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    df_cleaned = df.copy()
    data = request.get_json()
    action = data.get('action', 'clear')
    columns = data.get('columns', [])

    try:
        target_cols = columns if columns else df_cleaned.select_dtypes(include=['object', 'string']).columns.tolist()
        rows_affected = 0
        combined_invalid_mask = pd.Series([False] * len(df_cleaned), index=df_cleaned.index)

        for col in target_cols:
            # --- FIX ---
            # Replaced the overly strict 'is_string_dtype' check with one that also includes 'object' dtype.
            if col in df_cleaned.columns and (pd.api.types.is_string_dtype(df_cleaned[col]) or pd.api.types.is_object_dtype(df_cleaned[col])):
                try:
                    valid_mask = df_cleaned[col].str.match(EMAIL_REGEX, na=False)
                    # An invalid entry is one that is NOT valid AND is NOT null.
                    invalid_mask = (~valid_mask) & (df_cleaned[col].notna())

                    if action == 'clear':
                        count = invalid_mask.sum()
                        if count > 0:
                            rows_affected += int(count)
                            df_cleaned.loc[invalid_mask, col] = None
                    elif action == 'remove_row':
                        combined_invalid_mask |= invalid_mask
                except AttributeError:
                    print(f"Skipping email validation on non-string-like object column: {col}")
                    continue

        if action == 'remove_row':
            rows_before = len(df_cleaned)
            df_cleaned = df_cleaned[~combined_invalid_mask]
            rows_affected = rows_before - len(df_cleaned)
            message = f"{rows_affected} rows with invalid emails removed."
        else:
            message = f"{rows_affected} invalid email cells cleared."

        current_app.config['MAIN_DF'] = df_cleaned
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error during email validation: {str(e)}"}), 500