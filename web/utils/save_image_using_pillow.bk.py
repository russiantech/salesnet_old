from os import (path, listdir)
import secrets, hashlib

from werkzeug.utils import secure_filename
from flask import jsonify, current_app, flash

from PIL import Image, UnidentifiedImageError
regex = "([^\\s]+(\\.(?i)(jpe?g|png|gif|bmp))$)"

def uploader(file):
    try:
        if file and file.filename: #ensure a was actually uploaded & does not have empty names
            # Calculate a unique hash for the file content
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Check if a file with the same hash already exists
            upload_folder = path.join(current_app.root_path, 'static/images/uploads')
            for filename in listdir(upload_folder):
                if path.isfile(path.join(upload_folder, filename)):
                    existing_file_content = open(path.join(upload_folder, filename), 'rb').read()
                    existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
                    if existing_file_hash == file_hash:
                        return filename  # Return the existing filename if the same content exists

            # Generate a new unique filename
            random_hex = secrets.token_hex(2)
            _, f_ext = path.splitext(file.filename)
            fname = secure_filename(random_hex + f_ext).lower()
            mpath = path.join(upload_folder, fname)
            output_size = (200, 300)
            i = Image.open(file)
            i.thumbnail(output_size)
            i.save(mpath)

            return fname

        return jsonify({
            'response': 'Please choose a file to upload',
            'flash': 'alert-danger'
        })

    except UnidentifiedImageError:
        flash(f'Invalid File Type {file} ', 'alert-danger')
        return jsonify({
            'response': f'Sorry {file} Is Not Accepted',
            'flash': 'alert-danger'
        })


        
