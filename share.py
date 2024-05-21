from flask import Flask, request, render_template, send_from_directory, send_file, redirect, url_for, jsonify
from flask_socketio import SocketIO
from flask_dropzone import Dropzone
from flask_bootstrap import Bootstrap4
import collections
import os
import shutil
import re



app = Flask(__name__)
dropzone = Dropzone(app)
bootstrap = Bootstrap4(app)
socketio = SocketIO(app)

app.config.update(
    UPLOADED_PATH=os.getcwd() + '/uploads',
    DROPZONE_ALLOWED_FILE_TYPE='default',
    DROPZONE_MAX_FILE_SIZE=1000, # MB
    DROPZONE_MAX_FILES=50000, # Max number of files
)


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def get_upload_path(filename):
    return os.path.join(app.config['UPLOADED_PATH'], filename)

def list_paths(startpath):
    def nested_dict():
        return collections.defaultdict(nested_dict)
    files_dict = nested_dict()
    folders_list = []
    for root, dirs, files in os.walk(startpath):
        current_dict = files_dict
        rel_path = os.path.relpath(root, startpath)
        if rel_path != '.':
            path_parts = rel_path.split(os.sep)
            for part in path_parts:
                current_dict = current_dict[part]
            folders_list.append(rel_path.replace('\\', '/'))
        for file in files:
            path = os.path.join(root, file)
            if path.endswith('uploads\\uploaded files show up here'):
                continue
            current_dict[file] = path
    return files_dict, folders_list


@app.route('/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('file')
        folder = request.form.get('folder')
        if folder == None:
            folder = './'
        else:
            folder = os.path.join(app.config['UPLOADED_PATH'], folder)
        os.makedirs(folder, exist_ok=True)
        for f in files:
            f.save(os.path.join(folder, f.filename))
    paths, folders = list_paths(app.config['UPLOADED_PATH'])
    return render_template('upload.html', files=paths, folders=folders)




@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form.get('folder_name')
    if not re.match(r'^[\w-]+(\/[\w-]+)*$', folder_name):
        return "Invalid folder name. Please use only letters, numbers, underscores, and hyphens. Use '/' for nested folders.", 400
    os.makedirs(os.path.join(app.config['UPLOADED_PATH'], folder_name), exist_ok=True)
    return redirect(url_for('upload'))


@app.route('/delete_folder/<path:folder_name>', methods=['GET'])
def delete_folder(folder_name):
    shutil.rmtree(os.path.join(app.config['UPLOADED_PATH'], folder_name))
    return redirect(url_for('upload'))

@app.route('/files/<path:filename>', methods=['GET'])
def download(filename):
    path = os.path.join(app.config['UPLOADED_PATH'], filename)
    if os.path.isdir(path):
        shutil.make_archive(path, 'zip', path)
        return send_file(f'./uploads/{filename}.zip', as_attachment=True)
    else:
        return send_from_directory(app.config['UPLOADED_PATH'], filename, as_attachment=True)

@app.route('/delete/<path:filename>', methods=['GET'])
def delete(filename):
    remove_path(get_upload_path(filename))
    return redirect(url_for('upload'))


@app.route('/download_all', methods=['GET'])
def download_all():
    shutil.make_archive('uploads', 'zip', app.config['UPLOADED_PATH'])
    return send_file('uploads.zip', as_attachment=True)

@app.route('/delete_all', methods=['GET'])
def delete_all():
    for filename in os.listdir(app.config['UPLOADED_PATH']):
        remove_path(get_upload_path(filename))
    return redirect(url_for('upload'))




if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=8080)