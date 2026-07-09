import os
import sys
from pathlib import Path
from flask import Flask, send_from_directory

# This block is crucial for the packaged .exe to find its modules.
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)

# --- FIX: Import both shared objects from the 'backend.api' package ---
from backend.api import api_blueprint, socketio

# --- Path setup for Development and Packaged App ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = (BASE_DIR / "frontend").resolve()


# --- Flask App Initialization ---
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path='')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAIN_DF'] = None
app.config['FILENAME'] = None
app.config['HISTORY_TRACKER'] = None
app.config['UPLOAD_ID'] = None

# Initialize SocketIO with the Flask app
socketio.init_app(app)

# Register the API blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')


# --- SPA Routing ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    else:
        return send_from_directory(FRONTEND_DIR, 'index.html')


# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# --- Main Entry Point ---
if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)