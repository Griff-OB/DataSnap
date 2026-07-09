from flask import Blueprint
from flask_socketio import SocketIO

# --- FIX: Force a deterministic async driver that works reliably in frozen apps ---
# 'threading' is the most compatible choice for PyInstaller as it requires no extra packages.
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

api_blueprint = Blueprint("api", __name__)

# Import routes AFTER creating socketio/blueprint to prevent circular dependencies
from . import data_routes, cleaning_routes, analysis_routes, transform_routes, history_routes, session_routes, ai_routes