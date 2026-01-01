import os
import logging


def cleanup_temp_file(file_path: str):
    try:
        if os.path.exists(file_path): return os.remove(file_path)
    except Exception as e:
        logging.warning(f"Failed to cleanup temporary file {file_path}: {str(e)}")
