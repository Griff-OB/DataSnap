from flask import request, jsonify, current_app
from . import api_blueprint

@api_blueprint.route('/history', methods=['GET'])
def get_history():
    """Returns the list of historical actions."""
    tracker = current_app.config.get('HISTORY_TRACKER')
    if not tracker:
        return jsonify({"status": "success", "history": []})
    
    # Return in reverse chronological order so newest is first
    return jsonify({"status": "success", "history": tracker.get_history()[::-1]})

@api_blueprint.route('/history/revert', methods=['POST'])
def revert_to_history_version():
    """Reverts the main DataFrame to a specific snapshot from history."""
    tracker = current_app.config.get('HISTORY_TRACKER')
    df = current_app.config.get('MAIN_DF')

    if not tracker or df is None:
        return jsonify({"status": "error", "message": "History or data not available."}), 404

    data = request.get_json()
    history_id = data.get('id')
    if not history_id:
        return jsonify({"status": "error", "message": "History ID is required."}), 400

    # Revert to the version using your tracker's method
    snapshot_df = tracker.revert_to_version(history_id)

    if snapshot_df is not None:
        # Update the main DataFrame with the snapshot
        current_app.config['MAIN_DF'] = snapshot_df
        
        # Log this revert action itself as a new history item
        tracker.log_change(
            action="Revert",
            description=f"Reverted to state from an earlier action.",
            data_snapshot=snapshot_df
        )

        return jsonify({"status": "success", "message": "Successfully reverted to the selected state."})
    else:
        return jsonify({"status": "error", "message": "History snapshot not found."}), 404