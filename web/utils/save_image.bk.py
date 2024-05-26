from os import (environ, path, listdir)
import secrets, hashlib, cv2
import numpy as np

from werkzeug.utils import secure_filename
from flask import json, jsonify, current_app, flash, request


#as alternative to FileAllowed() I can also use this allowed_file()
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in environ.get('ALLOWED_EXTENSIONS')

def validate_(form, model, row):
    if model.query.filter_by(row=form).first():
        raise ValidationError(f'This very {form} has already been saved with another course.')


def upload_image(img_file):
    try:
         
        if  not img_file or img_file =='':
            return jsonify({ 
                'response': f'oops,You Must Select A File To Upload ',
                'flash':'alert-danger' }) 
        else: 
            img_file = img_file or request.files['images']
            random_hex = secrets.token_hex(8)
            _, f_ext = path.splitext(img_file.filename)
            #img_name = (random_hex + f_ext).lower()
            img_name = secure_filename(_ + random_hex + f_ext).lower()
            # Save the uploaded image to the uploads folder
            #img_path =  path.join(current_app.root_path, 'static/img/course/small', fname)
            #img_path = path.join(environ.get('uploadfolder'), img_name)
            img_path = path.join(current_app.root_path, 'static/images/items', fname)
            img_file.save(img_path)
            # Load and resize the uploaded image
            uploaded_image = cv2.imread(img_path)
            output_size = (300, 400)
            resized_image = cv2.resize(uploaded_image, output_size )
            # Save the resized image with a new name
            #new_img_path = path.join( environ.get('uploadfolder'), img_name )
            new_img_path = path.join(current_app.root_path, 'static/images/items', fname)
            cv2.imwrite(new_img_path, resized_image)
            return img_name
    except Exception as e:
        return flash(f'Invalid File Type {e} ')

""" def upload_image():
    if 'image' not in request.files:
        return "No image part"

    image_file = request.files['image']

    if image_file.filename == '':
        return "No selected image"

    if image_file:
        # Save the uploaded image to the uploads folder
        image_path = path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)

        # Load and resize the uploaded image using OpenCV and numpy
        uploaded_image = cv2.imread(image_path)
        new_height = 300
        new_width = 400
        resized_image = cv2.resize(uploaded_image, (new_width, new_height))

        # Save the resized image with a new name
        new_image_path = path.join(app.config['UPLOAD_FOLDER'], 'resized_' + image_file.filename)
        cv2.imwrite(new_image_path, resized_image)

        return "Image uploaded, resized, and saved as " + path.basename(new_image_path)
 """



from PIL import Image
from flask import current_app
from PIL import Image, UnidentifiedImageError
regex = "([^\\s]+(\\.(?i)(jpe?g|png|gif|bmp))$)"


# File path to store uploaded file hashes

#hashes_file_path = path.join(current_app.root_path, 'uploaded_hashes.txt')
#hashes_file_path = current_app.config['HASHES_FILE_PATH']
#hashes_file_path = path.join( path.abspath(path.dirname(__file__)), 'static/images/items', 'uploaded_hashes.txt')
#hashes_file_path = path.join( path.dirname(__file__), 'static/images/items', 'uploaded_hashes.txt')

# Calculate the absolute path to the uploaded_hashes.txt file
#file_dir = path.dirname(__file__)
#hashes_file_path = path.join(file_dir, 'static/images/items', 'uploaded_hashes.txt')

current_dir = path.dirname(path.abspath(__file__))
# Define the directory where you want to search for the file
hashes_file_path = path.join( environ.get('hashes_file_path'))

print(hashes_file_path)

# Initialize the list of uploaded file hashes
uploaded_file_hashes = []

# Load existing hashes from the file
if path.exists(hashes_file_path):
    with open(hashes_file_path, 'r') as f:
        uploaded_file_hashes = [line.strip() for line in f.readlines()]

def uploader(file):
    try:
        if file:
            # Calculate a unique hash for the file content
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Check if the file hash has been uploaded before
            if file_hash in uploaded_file_hashes:
                return get_existing_filename(file_hash)

            # Generate a new unique filename
            random_hex = secrets.token_hex(2)
            _, f_ext = path.splitext(file.filename)
            fname = secure_filename(random_hex + f_ext).lower()
            mpath = path.join(current_app.root_path, 'static/images/items', fname)
            output_size = (200, 300)
            i = Image.open(file)
            i.thumbnail(output_size)
            i.save(mpath)

            # Add the file hash to the list of uploaded file hashes
            uploaded_file_hashes.append(file_hash)

            # Write the updated list to the file
            with open(hashes_file_path, 'a') as f:
                f.write(file_hash + '\n')

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

# Function to check if a file with the same hash exists
def get_existing_filename(file_hash):
    upload_folder = path.join(current_app.root_path, 'static/images/items')

    for filename in listdir(upload_folder):
        if path.isfile(path.join(upload_folder, filename)):
            existing_file_content = open(path.join(upload_folder, filename), 'rb').read()
            existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
            if existing_file_hash == file_hash:
                return filename  # Return the existing filename if the same content exists

    return None  # No duplicate file found, return None


# Function to check if a file with the same hash exists
def check_duplicate_file(file_hash):
    upload_folder = path.join(current_app.root_path, 'static/images/items')
    for filename in listdir(upload_folder):
        if path.isfile(path.join(upload_folder, filename)):
            existing_file_content = open(path.join(upload_folder, filename), 'rb').read()
            existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
            if existing_file_hash == file_hash:
                return filename  # Return the existing filename if the same content exists

    return None  # No duplicate file found, return None

def uploader4(file):
    try:
        if file:
            # Calculate a unique hash for the file content
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Check if a file with the same hash exists
            existing_filename = check_duplicate_file(file_hash)
            
            if existing_filename:
                return existing_filename

            # Generate a new unique filename
            random_hex = secrets.token_hex(2)
            _, f_ext = path.splitext(file.filename)
            fname = secure_filename(random_hex + f_ext).lower()
            mpath = path.join(current_app.root_path, 'static/images/items', fname)
            output_size = (200, 100)
            i = Image.open(file)
            i.thumbnail(output_size)
            i.save(mpath)

            return fname

        return jsonify({
            'response': 'Please choose a file to upload',
            'flash': 'alert-danger'
        })

    except UnidentifiedImageError:
        #flash(f'Invalid Image: {file} ')
        return jsonify({
            'response': f'Sorry {file} Is Not Accepted',
            'flash': 'alert-danger'
        })

def uploader3(file):
    try:
        if file:
            random_hex = secrets.token_hex(2)
            _, f_ext = path.splitext(file.filename)
            fname = secure_filename(_ + random_hex + f_ext).lower()
            mpath = path.join(current_app.root_path, 'static/images/items', fname)
            output_size = (200, 300)
            i = Image.open(file)
            i.thumbnail(output_size)
            i.save(mpath)
            if fname and mpath:
                return fname 
        return jsonify({ 
                'response': f'Pls Choose File To Upload',
                'flash':'alert-danger' }) 
    except UnidentifiedImageError:
        flash(f'Invalid File Type {file} ')
        #return flash(f'Invalid File Type {file} ')
        return jsonify({ 
                'response': f'Sorry {file} Is Not Accepted',
                'flash':'alert-danger' }) 

def upload_multiple(filelist):
    try:
        if not (filelist or request.files.getlist('images')):
            
            return jsonify({ 
                'response': f' "file is uploaded',
                'flash':'alert-danger' }) 

        files = (filelist or request.files.getlist('images'))
        uploaded_filenames = [ uploader(f) for f in files if f]

        if uploaded_filenames:
            return json.dumps(uploaded_filenames)
            #return uploaded_filenames
        
        return jsonify({ 
            'response': f'Sorry Upload Failed!!',
            'flash':'alert-danger' }) 

    except UnidentifiedImageError:
        flash(f'Invalid File Type {file} ')
        #return flash(f'Invalid File Type {file} ')
        return jsonify({ 
                'response': f'Sorry {file} Is Not Accepted',
                'flash':'alert-danger' }) 

def upload_multiple2():
    try:
        if 'images' not in request.files:
            return jsonify({ 
                'response': f' "images" missing ',
                'flash':'alert-danger' }) 
        files = request.files.getlist('images')
        uploaded_filenames = []
        for f in files:
            uploaded = uploader(f)
            if uploaded:
                uploaded_filenames.append(uploaded)
                return uploaded_filenames

            return jsonify({ 
                'response': f'Sorry Upload Failed!!',
                'flash':'alert-danger' }) 

    except UnidentifiedImageError:
        flash(f'Invalid File Type {file} ')
        #return flash(f'Invalid File Type {file} ')
        return jsonify({ 
                'response': f'Sorry {file} Is Not Accepted',
                'flash':'alert-danger' }) 



from flask import request, redirect, url_for
from PIL import Image
import os
import uuid

# Function to resize an image
def resize_image(file, max_size=(800, 600)):
    img = Image.open(file)
    img.thumbnail(max_size)
    return img
# Function to generate a unique filename
def generate_unique_filename(filename):
    ext = filename.split('.')[-1]
    unique_filename = str(uuid.uuid4().hex) + '.' + ext
    return unique_filename

def upload_file():
    if 'images' not in request.files:
        return redirect(request.url)
    files = request.files.getlist('images')
    for file in files:
        if file:
            # Resize the image before saving it
            resized_img = resize_image(file.stream)
            # Generate a unique filename
            unique_filename = generate_unique_filename(file.filename)
            # Save the resized image with the unique filename
            resized_img.save(path.join('uploads', unique_filename))
    return unique_filename
        
