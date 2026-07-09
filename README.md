# DataSnap — Desktop Data Cleaning & Analysis

**DataSnap** is a desktop data‑cleaning and analysis app built with **Electron** (UI) and **Python (Flask + Pandas)**. It includes fast data preview, robust cleaning & transformation tools, rich profiling, and an optional **local AI assistant** (Llama via `llama-cpp-python`) that keeps your data fully offline.

![DataSnap Screenshot](app/frontend/assets/screenshot.png)

---

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1) Clone](#1-clone)
  - [2) Python Backend](#2-python-backend)
  - [3) Node--Electron Frontend](#3-node--electron-frontend)
  - [4) Run the App](#4-run-the-app)
- [First Run: Download the AI Model](#first-run-download-the-ai-model)
- [Project Structure](#project-structure)
- [Usage Tips](#usage-tips)
- [Contributing](#contributing)
- [License](#license)
- [Notes](#notes)

---

## Features
- **Intuitive Data Preview** — Load, view, sort, and filter large datasets in a fast, virtualized table.
- **Comprehensive Profiling** — Column stats, data‑quality scores, and PII detection.
- **Cleaning Tools**
  - Handle missing values (drop, fill with mean/median/custom).
  - Remove duplicate rows.
  - Outlier handling (IQR).
  - String ops (trim/upper/lower).
  - Find & replace with regex.
- **Transformations** — Sort, group/aggregate, calculated columns.
- **Local AI Assistant** — Download a local Llama model to ask data questions and get cleaning suggestions (fully offline).
- **Session Management** — Save/restore your progress to a session file.
- **Export** — CSV, Excel (XLSX), JSON, Parquet.
- **Themes** — Multiple color themes (dark included).

---

## Tech Stack
- **Desktop:** Electron
- **Backend:** Flask + Flask‑SocketIO
- **Python:** 3.9–3.11, Pandas
- **Local AI:** Llama 3.2 via `llama-cpp-python`
- **Frontend:** HTML, CSS, JavaScript
- **Table:** Tabulator
- **Charts:** Chart.js

---

## Prerequisites
1. **Node.js (v18+)** — <https://nodejs.org/>
2. **Python (3.9–3.11)** — <https://www.python.org/>
3. **C/C++ Build Tools** (needed for `llama-cpp-python`)
   - **Windows:** Install **Visual Studio Community** → workload **“Desktop development with C++”**
   - **macOS:** `xcode-select --install`
   - **Debian/Ubuntu:** `sudo apt-get update && sudo apt-get install build-essential`

---

## Installation

### 1) Clone
```bash
git clone https://github.com/OBrian-bit/DataSnap.git
cd DataSnap/data-wrangler
```

### 2) Python Backend
```bash
cd app/backend

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
.env\Scriptsctivate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3) Node / Electron Frontend
```bash
# from app/backend go back to project root
cd ../..
npm install
```

### 4) Run the App
```bash
npm start
```
This starts the Flask backend and launches the Electron desktop app.

---

## First Run: Download the AI Model
The Llama model is **not** stored in the repo (it’s large). After launch:

1. Open the **AI Chat** tab.  
2. Click **Download A.I. model**.  
3. A background download (~2 GB) will start with a progress bar.  
4. When complete, chat becomes available. *(One‑time setup per machine.)*

> Your data never leaves your device; the model runs 100% locally via `llama-cpp-python`.

---

## Project Structure
```text
data-wrangler/
├── app/
│   ├── backend/
│   │   ├── api/              # Flask API routes
│   │   ├── models/           # Local model download target (gitignored)
│   │   ├── temp_uploads/     # Chunked file temp storage
│   │   ├── utils/            # Profiling, PII, helpers
│   │   ├── app.py            # Flask entry
│   │   └── requirements.txt  # Python deps
│   └── frontend/
│       ├── css/
│       ├── js/
│       ├── lib/
│       └── index.html        # Main UI
├── main.js                   # Electron main process
├── package.json              # Node deps & scripts
└── README.md                 # This file
```

---

## Usage Tips
- **Sessions:** Use **Save Session** to export your work as a `.json` session file; **Load Session** to resume later.
- **Exports:** Choose your format (CSV/XLSX/JSON/Parquet) in the **Export** panel.
- **Themes:** Switch themes (incl. dark) from the theme selector in the header.
- **AI:** The model is downloaded once, but you can delete the `app/backend/models/` folder to re-download or swap models later.

---

## Contributing
PRs and issues are welcome! If you find a bug or have a feature request, please open an issue.

---

## License
**MIT** — see `LICENSE` for details.

---

## Notes
- Large models/binaries are **not** stored in the repository (GitHub’s 100 MB limit). The app downloads the model to `app/backend/models/` at runtime and keeps it locally.
- If building `llama-cpp-python` fails, recheck your C++ toolchain and try a clean virtual environment.
