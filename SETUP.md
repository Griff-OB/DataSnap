# Data Wrangler Setup Instructions

## Prerequisites
Before running the Data Wrangler application, ensure you have the following installed:

### Python Requirements
- Python 3.8 or higher
- pip (Python package manager)

### Node.js Requirements
- Node.js 14 or higher
- npm (Node package manager)

## Installation Steps
### 1. Install Python Dependencies
Navigate to the backend directory and install the required Python packages:
```bash
cd app/backend
pip install -r requirements.txt
cd ../..
```

### 2. Install Node.js Dependencies
Install the required Node.js packages:
```bash
npm install
```

### 3. Download Frontend Libraries
The application requires two external JavaScript libraries:

#### Tabulator (Interactive Table Library)
1. Download Tabulator from: https://github.com/olifolkerd/tabulator/releases
2. Extract the downloaded file
3. Copy `tabulator.min.css` to `app/frontend/lib/tabulator/`
4. Copy `tabulator.min.js` to `app/frontend/lib/tabulator/`

#### Chart.js (Charting Library)
1. Download Chart.js from: https://www.chartjs.org/
2. Extract the downloaded file
3. Copy `chart.min.js` to `app/frontend/lib/chart.js/`

### 4. Create App Icon (Optional)
If you want to customize the app icon:
1. Create a 512x512 PNG image
2. Save it as `app-icon.png` in the `app/frontend/assets/icons/` directory

## Running the Application
### Development Mode
#### Option 1: Separate Processes
1. Start the Flask backend server:
```bash
cd app/backend
python app.py
```
2. In a separate terminal, start the Electron application:
```bash
npm start
```
#### Option 2: Concurrent Development
Use the built-in concurrent development mode:
```bash
npm run dev
```
### Production Build
To create a distributable desktop application:
```bash
npm run build
```
The built application will be available in the `dist/` directory.

## Troubleshooting
### Common Issues
#### Python Module Not Found
If you encounter import errors for Python modules:
```bash
cd app/backend
pip install -r requirements.txt --upgrade
```
#### Node.js Module Not Found
If you encounter Node.js module errors:
```bash
npm install
```
#### Port Already in Use
If port 5000 is already in use:
1. Change the port in `app/backend/app.py`
2. Update the URL in `main.js` to match the new port

#### Frontend Libraries Missing
If the application fails to load due to missing libraries:
1. Ensure Tabulator and Chart.js are properly downloaded
2. Check that the files are in the correct directories:
- `app/frontend/lib/tabulator/tabulator.min.css`
- `app/frontend/lib/tabulator/tabulator.min.js`
- `app/frontend/lib/chart.js/chart.min.js`

## File Format Support
The application supports the following file formats:
- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel files
- **JSON** (.json) - JSON files (lines format)
- **Parquet** (.parquet) - Apache Parquet files
- **TSV** (.tsv) - Tab-separated values

## System Requirements
### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 100MB free space
- **OS**: Windows 10, macOS 10.14, or Ubuntu 18.04

### Recommended Requirements
- **RAM**: 8GB or more
- **Storage**: 1GB free space (for temporary files)
- **OS**: Latest version of Windows, macOS, or Linux

## Getting Help
If you encounter any issues:
1. Check the browser console for error messages
2. Review the Python server output in the terminal
3. Ensure all dependencies are properly installed
4. Verify that the frontend libraries are correctly placed

For additional support, please refer to the README.md file or open an issue on the project repository.
