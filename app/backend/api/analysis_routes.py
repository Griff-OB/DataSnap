# data-wrangler/app/backend/api/analysis_routes.py

import pandas as pd
import numpy as np
from flask import request, jsonify, current_app

# --- FIX: Use relative imports to find the utils package ---
from ..utils.data_profiler import DataProfiler
from ..utils.pii_scanner import PIIScanner
from . import api_blueprint, socketio

@api_blueprint.route('/profile', methods=['GET'])
def get_data_profile():
    df = current_app.config.get('MAIN_DF')
    if df is None:
        return jsonify({"status": "error", "message": "No data loaded."}), 404

    profiler = DataProfiler()
    pii_scanner = PIIScanner()

    try:
        # Basic stats
        total_rows = len(df)
        total_columns = len(df.columns)
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()

        # Column-level analysis
        column_profiles = []
        pii_detected = False
        pii_summary = {}

        for col in df.columns:
            col_data = df[col]
            col_profile = {
                'name': col,
                'dataType': str(col_data.dtype),
                'uniqueCount': col_data.nunique(),
                'nullCount': int(col_data.isnull().sum()),
                'nullPercentage': round((col_data.isnull().sum() / len(col_data)) * 100, 2)
            }

            # Numeric stats
            if pd.api.types.is_numeric_dtype(col_data):
                numeric_stats = col_data.describe()
                col_profile.update({
                    'min': float(numeric_stats['min']) if not pd.isna(numeric_stats['min']) else None,
                    'max': float(numeric_stats['max']) if not pd.isna(numeric_stats['max']) else None,
                    'mean': float(numeric_stats['mean']) if not pd.isna(numeric_stats['mean']) else None,
                    'std': float(numeric_stats['std']) if not pd.isna(numeric_stats['std']) else None,
                    'median': float(numeric_stats['50%']) if not pd.isna(numeric_stats['50%']) else None
                })

            # PII detection for string columns
            if pd.api.types.is_string_dtype(col_data):
                sample_data = col_data.dropna().astype(str).head(100)
                pii_results = pii_scanner.scan_column(sample_data, col)
                if pii_results['detected']:
                    pii_detected = True
                    # Store the detailed detection results
                    pii_summary[col] = pii_results['types']
                    col_profile['piiDetected'] = pii_results['detected']
            
            column_profiles.append(col_profile)

        # Calculate quality scores
        completeness_score = max(0, 100 - (missing_cells / (total_rows * total_columns)) * 100)
        uniqueness_score = max(0, 100 - (duplicate_rows / total_rows) * 100)
        consistency_score = 85 # Simplified calculation
        validity_score = 90 # Simplified calculation

        overall_score = (completeness_score + uniqueness_score + consistency_score + validity_score) / 4

        # Generate recommendations
        recommendations = []
        if completeness_score < 80:
            recommendations.append("Consider handling missing values")
        if uniqueness_score < 90:
            recommendations.append("Remove duplicate rows to improve data quality")
        if pii_detected:
            recommendations.append("PII data detected - consider anonymization")

        return jsonify({
            "status": "success",
            "profile": {
                "totalRows": total_rows,
                "totalColumns": total_columns,
                "missingCells": int(missing_cells),
                "duplicateRows": int(duplicate_rows),
                "overallScore": round(overall_score, 2),
                "completenessScore": round(completeness_score, 2),
                "uniquenessScore": round(uniqueness_score, 2),
                "consistencyScore": round(consistency_score, 2),
                "validityScore": round(validity_score, 2),
                "columns": column_profiles,
                "piiDetected": pii_detected,
                "piiSummary": pii_summary,
                "recommendations": recommendations
            }
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Error profiling data: {str(e)}"}), 500