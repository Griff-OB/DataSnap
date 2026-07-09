const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

/**
 * Creates the main application window.
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            // Securely expose IPC functions to the renderer process
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
        },
        icon: path.join(__dirname, 'app', 'frontend', 'assets', 'icons', 'app-icon.png'),
        show: false
    });

    // Start the Python backend server
    startPythonServer();

    // Attempt to load the frontend from the Python server.
    // We will add retry logic in case the server isn't up yet.
    loadWithRetry('http://localhost:5000');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        // For debugging development environment
        // mainWindow.webContents.openDevTools(); 
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        if (pythonProcess) {
            console.log('Killing Python process...');
            pythonProcess.kill();
            pythonProcess = null;
        }
    });
}

/**
 * Starts the Python backend server.
 * It intelligently runs the pre-compiled executable in production (packaged app)
 * and the raw Python script in development.
 */
function startPythonServer() {
    if (app.isPackaged) {
        // --- PRODUCTION MODE ---
        // The Python app is a pre-compiled executable.
        const backendAppName = process.platform === 'win32' ? 'app.exe' : 'app';
        // The executable is placed in 'resources/app-backend' by electron-builder.
        const executablePath = path.join(process.resourcesPath, 'app-backend', backendAppName);
        
        console.log(`Starting packaged backend at: ${executablePath}`);
        pythonProcess = spawn(executablePath, [], {
            cwd: path.dirname(executablePath) // Set working directory to the executable's location
        });

    } else {
        // --- DEVELOPMENT MODE ---
        // Run the Python script directly using python's module flag '-m'
        // to ensure 'from backend...' imports work correctly.
        const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
        // The CWD must be the root of the package, which is the 'app' directory.
        const projectRoot = path.join(__dirname, 'app');

        console.log(`Starting development backend with: ${pythonExecutable} -m backend.app`);
        pythonProcess = spawn(pythonExecutable, ['-m', 'backend.app'], {
            cwd: projectRoot,
            stdio: 'pipe' // Pipe stdio to Electron's console for debugging
        });
    }

    // --- Listen for output and errors from the Python process ---
    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        if (code !== 0 && mainWindow) {
            // Send an error message to the renderer if the process crashes
            mainWindow.webContents.send('python-error', `Python server exited unexpectedly with code ${code}`);
        }
    });
    
    pythonProcess.on('error', (error) => {
        console.error('Failed to start Python server:', error);
        if (mainWindow) {
            mainWindow.webContents.send('python-error', `Failed to start Python server: ${error.message}`);
        }
    });
}

/**
 * Tries to load a URL, retrying every 100ms if it fails.
 * This is useful to wait for the Python backend to start.
 * @param {string} url - The URL to load.
 */
function loadWithRetry(url) {
    mainWindow.loadURL(url).catch(() => {
        console.log('Failed to load URL, retrying in 100ms...');
        setTimeout(() => {
            if (mainWindow && !mainWindow.isDestroyed()) {
                loadWithRetry(url);
            }
        }, 100);
    });
}

// --- Electron App Lifecycle ---
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// --- IPC Handlers for Renderer Communication ---
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});

ipcMain.handle('get-app-path', () => {
    return app.getAppPath();
});

ipcMain.handle('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, options);
    return result;
});