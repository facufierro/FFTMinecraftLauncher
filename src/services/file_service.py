import logging
import os
import shutil
import zipfile
import io


class FileService:
    def __init__(self):
        logging.debug("Initializing FileService")

    def replace_files_in_folder(self, zip_file, target_folder):
        # replace files with the same name in target_folder with files from zip_file
        try:
            logging.debug(f"Replacing files in {target_folder} with {zip_file}")
            zf = io.BytesIO(zip_file) if isinstance(zip_file, bytes) else zip_file
            with zipfile.ZipFile(zf, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        continue
                    target_path = os.path.join(target_folder, file_info.filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(file_info) as source_file:
                        with open(target_path, "wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
            logging.debug(f"Files replaced in {target_folder}")
        except Exception as e:
            logging.error(f"Failed to replace files: {e}")
            raise

    def replace_folder(self, zip_file, target_folder):
        # replace the entire target_folder with files from zip_file
        try:
            logging.debug(f"Replacing folder {target_folder} with {zip_file}")
            if os.path.exists(target_folder):
                shutil.rmtree(target_folder)
            zf = io.BytesIO(zip_file) if isinstance(zip_file, bytes) else zip_file
            with zipfile.ZipFile(zf, "r") as zip_ref:
                zip_ref.extractall(target_folder)
            logging.debug(f"Replaced folder: {target_folder}")
        except Exception as e:
            logging.error(f"Failed to replace folder: {e}")
            raise

    def add_file_to_folder(self, file_path, target_folder):
        # add a file to the target folder
        try:
            logging.debug(f"Adding file {file_path} to {target_folder}")
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            shutil.copy(file_path, target_folder)
            logging.debug(f"Added file: {file_path} to {target_folder}")
        except Exception as e:
            logging.error(f"Failed to add file: {e}")
            raise

    def add_files_to_folder(self, zip_file, target_folder):
        # add files from zip_file to target_folder if they don't exist, or replace them if they do
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        try:
            logging.debug(f"Adding files from {zip_file} to {target_folder}")
            zf = io.BytesIO(zip_file) if isinstance(zip_file, bytes) else zip_file
            with zipfile.ZipFile(zf, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        continue
                    target_path = os.path.join(target_folder, file_info.filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(file_info) as source_file:
                        with open(target_path, "wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
            logging.debug(f"Files added from {zip_file} to {target_folder}")
        except Exception as e:
            logging.error(f"Failed to add files: {e}")
            raise

    def replace_file(self, file_path, target_folder):
        # replace a file in the target folder
        try:
            logging.debug(f"Replacing file {file_path} in {target_folder}")
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            target_path = os.path.join(target_folder, os.path.basename(file_path))
            shutil.copy(file_path, target_path)
            logging.debug(f"Replaced file: {file_path} in {target_folder}")
        except Exception as e:
            logging.error(f"Failed to replace file: {e}")
            raise

    def save_file_content(self, content, file_path):
        """Save content (bytes or text) to a file"""
        try:
            logging.debug(f"Saving content to {file_path}")
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write content based on type
            if isinstance(content, bytes):
                with open(file_path, "wb") as f:
                    f.write(content)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            logging.debug(f"Saved content to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save content to {file_path}: {e}")
            raise
