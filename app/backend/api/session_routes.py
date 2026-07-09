import json
import os
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from flask import request, current_app, Response, jsonify


from . import api_blueprint, socketio


# ---------- Helpers ----------

def _df_to_json_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Make a DataFrame strictly JSON-serializable:
    - datetimes -> ISO 8601 strings
    - timedeltas -> strings
    - categoricals -> objects
    - numpy scalars -> Python natives
    - NaN/NaT/±Inf -> None
    """
    df2 = df.copy()

    # Normalize special dtypes to strings
    for col in df2.columns:
        s = df2[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            # drop tz to keep it simple; then ISO
            try:
                df2[col] = s.dt.tz_localize(None).dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                # if already tz-naive or mixed, fallback to astype string
                df2[col] = s.astype("string")
        elif pd.api.types.is_timedelta64_dtype(s):
            df2[col] = s.astype("string")
        elif pd.api.types.is_categorical_dtype(s):
            df2[col] = s.astype("object")

    # Replace NaN/NaT/±Inf with None
    df2 = df2.replace({np.nan: None, np.inf: None, -np.inf: None})

    # Ensure numpy scalars become python natives
    def to_native(v):
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            # after replace above, remaining floats are finite
            return float(v)
        if isinstance(v, (np.bool_,)):
            return bool(v)
        return v

    records = []
    for rec in df2.to_dict(orient="records"):
        records.append({k: to_native(v) for k, v in rec.items()})
    return records


def _make_strict_json_response(payload: Dict[str, Any], status: int = 200) -> Response:
    """Serialize with allow_nan=False to prevent invalid JSON (NaN/Infinity)."""
    json_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return Response(json_text, status=status, mimetype="application/json")


# ---------- Routes ----------

@api_blueprint.route('/session/save', methods=['POST'])
def save_session():
    df: pd.DataFrame = current_app.config.get('MAIN_DF')
    if df is None:
        return _make_strict_json_response({"status": "error", "message": "No data loaded."}, 404)

    try:
        filename = current_app.config.get('FILENAME') or "Untitled Dataset"
        data_records = _df_to_json_records(df)

        session_data = {
            "filename": filename,
            "savedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "shape": {"rows": len(df), "cols": len(df.columns)},
            "dtypes": {c: str(df[c].dtype) for c in df.columns},
            "data": data_records,
            "version": 1,  # increment if you change the schema
        }

        # IMPORTANT: return strict JSON (no NaN tokens)
        return _make_strict_json_response({
            "status": "success",
            "message": "Session saved successfully",
            **session_data
        })

    except Exception as e:
        return _make_strict_json_response({"status": "error", "message": f"Error saving session: {e}"}, 500)


@api_blueprint.route('/session/load', methods=['POST'])
def load_session():
    try:
        if 'session_file' not in request.files:
            return _make_strict_json_response({"status": "error", "message": "No session file provided."}, 400)

        session_file = request.files['session_file']
        if not session_file.filename:
            return _make_strict_json_response({"status": "error", "message": "No file selected."}, 400)

        # Read and parse strictly
        raw = session_file.read()
        try:
            text = raw.decode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            text = raw if isinstance(raw, str) else raw.decode('utf-8', errors='replace')

        session_data = json.loads(text)

        # Validate minimal structure
        if not isinstance(session_data, dict) or "data" not in session_data:
            return _make_strict_json_response({"status": "error", "message": "Invalid session file format."}, 400)
        if not isinstance(session_data["data"], list):
            return _make_strict_json_response({"status": "error", "message": "'data' must be a list of records."}, 400)

        # Recreate DataFrame
        df = pd.DataFrame(session_data["data"])

        # Update app state
        filename = session_data.get("filename") or "Loaded Session"
        current_app.config['MAIN_DF'] = df
        current_app.config['FILENAME'] = filename

        # History tracker is optional
        tracker = current_app.config.get('HISTORY_TRACKER')
        if tracker:
            try:
                if hasattr(tracker, "clear_history"):
                    tracker.clear_history()
                if hasattr(tracker, "log_change"):
                    tracker.log_change(
                        action="Session Load",
                        description=f"Loaded session file '{filename}'",
                        data_snapshot=df
                    )
            except Exception as log_err:
                # Do not fail the load on tracker issues
                current_app.logger.warning(f"History tracker error: {log_err}")

        return _make_strict_json_response({
            "status": "success",
            "message": "Session loaded successfully",
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns)
        })

    except json.JSONDecodeError as je:
        return _make_strict_json_response({"status": "error", "message": f"Invalid JSON: {je}"}, 400)
    except Exception as e:
        return _make_strict_json_response({"status": "error", "message": f"Error loading session: {e}"} , 500)
