import pandas as pd
from flask import request, jsonify, current_app

from . import api_blueprint, socketio

@api_blueprint.route('/transform/sort', methods=['POST'])
def sort_data():
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    data = request.get_json()
    columns = data.get('columns', [])
    ascending = data.get('ascending', True)

    try:
        if not columns:
            return jsonify({"status": "error", "message": "No columns specified for sorting."}), 400

        df_sorted = df.sort_values(by=columns, ascending=ascending)
        current_app.config['MAIN_DF'] = df_sorted

        return jsonify({
            "status": "success",
            "message": f"Data sorted by columns: {', '.join(columns)}",
            "sort_order": "ascending" if ascending else "descending"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error sorting data: {str(e)}"}), 500

@api_blueprint.route('/transform/group-by', methods=['POST'])
def group_by_data():
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    data = request.get_json()
    group_columns = data.get('group_columns', [])
    agg_column = data.get('agg_column')
    agg_function = data.get('agg_function', 'sum')

    try:
        if not group_columns:
            return jsonify({"status": "error", "message": "No group columns specified."}), 400

        if agg_column:
            agg_dict = {agg_column: agg_function}
        else:
            # Aggregate all numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            agg_dict = {col: agg_function for col in numeric_cols}

        df_grouped = df.groupby(group_columns).agg(agg_dict).reset_index()
        current_app.config['MAIN_DF'] = df_grouped

        return jsonify({
            "status": "success",
            "message": f"Data grouped by {', '.join(group_columns)} with {agg_function} aggregation",
            "original_shape": df.shape,
            "new_shape": df_grouped.shape
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error grouping data: {str(e)}"}), 500

@api_blueprint.route('/transform/pivot', methods=['POST'])
def pivot_data():
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    data = request.get_json()
    index_column = data.get('index_column')
    columns_column = data.get('columns_column')
    values_column = data.get('values_column')
    agg_function = data.get('agg_function', 'sum')

    try:
        if not all([index_column, columns_column, values_column]):
            return jsonify({"status": "error", "message": "Missing required pivot parameters."}), 400

        df_pivot = df.pivot_table(
            index=index_column,
            columns=columns_column,
            values=values_column,
            aggfunc=agg_function,
            fill_value=0
        ).reset_index()

        current_app.config['MAIN_DF'] = df_pivot

        return jsonify({
            "status": "success",
            "message": f"Data pivoted with {index_column} as index, {columns_column} as columns",
            "original_shape": df.shape,
            "new_shape": df_pivot.shape
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error pivoting data: {str(e)}"}), 500

@api_blueprint.route('/transform/calculated-column', methods=['POST'])
def add_calculated_column():
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    data = request.get_json()
    column_name = data.get('column_name')
    expression = data.get('expression')

    try:
        if not column_name or not expression:
            return jsonify({"status": "error", "message": "Column name and expression are required."}), 400

        # Safe evaluation of expression
        df[column_name] = df.eval(expression)
        current_app.config['MAIN_DF'] = df

        return jsonify({
            "status": "success",
            "message": f"Calculated column '{column_name}' added with expression: {expression}",
            "new_column": column_name
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error adding calculated column: {str(e)}"}), 500
