import uuid
from datetime import datetime
from . import api_blueprint, socketio

class HistoryTracker:
    def __init__(self):
        self.history = []
        # Snapshots will be stored as { 'snapshot_id': DataFrame }
        self.snapshots = {}

    def log_change(self, action, description, data_snapshot=None):
        """Log a data change with snapshot."""
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'description': description
        }

        if data_snapshot is not None:
            snapshot_id = str(uuid.uuid4())
            # FIX: Store a deep COPY of the DataFrame, not a reference.
            # This is critical for preserving the state at this exact moment.
            self.snapshots[snapshot_id] = data_snapshot.copy()
            entry['snapshot_id'] = snapshot_id

        self.history.append(entry)
        return entry['id']

    def get_history(self):
        """Get complete history."""
        return self.history

    def get_snapshot(self, snapshot_id):
        """Get data snapshot by ID."""
        return self.snapshots.get(snapshot_id)

    def revert_to_version(self, history_id):
        """Revert to a specific version."""
        target_entry = None
        for entry in self.history:
            if entry['id'] == history_id:
                target_entry = entry
                break

        if not target_entry or 'snapshot_id' not in target_entry:
            return None

        snapshot = self.get_snapshot(target_entry['snapshot_id'])

        # FIX: Return a COPY of the snapshot to prevent the user
        # from accidentally modifying the historical record after reverting.
        return snapshot.copy() if snapshot is not None else None

    def clear_history(self):
        """Clear all history and snapshots."""
        self.history = []
        self.snapshots = {}

    def export_history(self):
        """Export history to JSON."""
        return {
            'history': self.history,
            # Snapshots are not exported as they are large DataFrame objects
        }

    def import_history(self, history_data):
        """Import history from JSON."""
        # This is more complex as it would require deserializing DataFrames
        self.history = history_data.get('history', [])
        self.snapshots = {} # Snapshots are not imported