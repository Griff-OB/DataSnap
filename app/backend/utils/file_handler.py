import os
import pandas as pd
from pathlib import Path

class FileHandler:
    def __init__(self, upload_dir='temp_uploads'):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    def get_supported_formats(self):
        """Get list of supported file formats"""
        return {
            '.csv': 'CSV files',
            '.xlsx': 'Excel files',
            '.xls': 'Excel files (old format)',
            '.json': 'JSON files',
            '.parquet': 'Parquet files',
            '.tsv': 'TSV files'
        }

    def is_supported_format(self, filename):
        """Check if file format is supported"""
        return Path(filename).suffix.lower() in self.get_supported_formats()

    def save_chunk(self, chunk_data, upload_id, chunk_index):
        """Save a file chunk"""
        chunk_filename = f"{upload_id}_chunk_{chunk_index}"
        chunk_path = self.upload_dir / chunk_filename

        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)

        return chunk_path

    def reassemble_file(self, upload_id, total_chunks, original_filename):
        """Reassemble chunks into complete file"""
        reassembled_path = self.upload_dir / original_filename

        with open(reassembled_path, 'wb') as final_file:
            for i in range(total_chunks):
                chunk_path = self.upload_dir / f"{upload_id}_chunk_{i}"
                if chunk_path.exists():
                    with open(chunk_path, 'rb') as chunk_file:
                        final_file.write(chunk_file.read())
        
        return reassembled_path

    def cleanup_chunks(self, upload_id, total_chunks):
        """Clean up chunk files"""
        for i in range(total_chunks):
            chunk_path = self.upload_dir / f"{upload_id}_chunk_{i}"
            if chunk_path.exists():
                chunk_path.unlink()

    def load_file(self, file_path):
        """Load file into pandas DataFrame"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        try:
            if extension == '.csv':
                return pd.read_csv(file_path)
            elif extension == '.tsv':
                return pd.read_csv(file_path, sep='\t')
            elif extension in ['.xlsx', '.xls']:
                return pd.read_excel(file_path, engine='openpyxl')
            elif extension == '.json':
                return pd.read_json(file_path, lines=True)
            elif extension == '.parquet':
                return pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {extension}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_path.name}: {e}")

    def save_session(self, session_data, session_id):
        """Save session data to file"""
        session_filename = f"session_{session_id}.json"
        session_path = self.upload_dir / session_filename

        with open(session_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(session_data, f, indent=2, default=str)

        return session_path

    def load_session(self, session_file):
        """Load session data from file"""
        import json
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def cleanup_temp_files(self):
        """Clean up all temporary files"""
        for file_path in self.upload_dir.glob('*'):
            if file_path.is_file():
                file_path.unlink()
