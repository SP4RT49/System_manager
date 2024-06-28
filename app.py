import os
import socket
import platform
import psutil
import json
import locale
import webbrowser
from flask import Flask, jsonify, request, render_template, g

app = Flask(__name__)

def load_translations(language):
    with open(f'translations/{language}.json', encoding='utf-8') as json_file:
        translations = json.load(json_file)
    return translations

def get_system_language():
    system_locale = locale.getdefaultlocale()
    language_code = system_locale[0][:2]
    return language_code if language_code in ['en', 'fr'] else 'en'

@app.before_request
def before_request():
    language = request.args.get('lang', get_system_language())
    g.translations = load_translations(language)
    g.lang = language

@app.route('/')
def index():
    return render_template('index.html', translations=g.translations, lang=g.lang)

@app.route('/disk_usage')
def disk_usage():
    partitions = psutil.disk_partitions()
    usage = []
    for partition in partitions:
        if os.name == 'nt':
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
        usage.append({
            'device': partition.device,
            'mountpoint': partition.mountpoint,
            'fstype': partition.fstype,
            'total': psutil.disk_usage(partition.mountpoint).total,
            'used': psutil.disk_usage(partition.mountpoint).used,
            'free': psutil.disk_usage(partition.mountpoint).free,
            'percent': psutil.disk_usage(partition.mountpoint).percent
        })
    return jsonify(usage)

@app.route('/system_info')
def system_info():
    info = {
        'user_name': os.getlogin(),
        'host_name': socket.gethostname(),
        'host_ip': socket.gethostbyname(socket.gethostname()),
        'platform_name': platform.system(),
        'platform_version': platform.version(),
        'platform_architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(logical=False),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'memory_used': psutil.virtual_memory().used,
        'memory_percent': psutil.virtual_memory().percent,
        'cpu_percent': psutil.cpu_percent(interval=1),
        'home_dir': os.path.expanduser("~"),
        'temp_dir': os.getenv('TEMP'),
        'boot_time': psutil.boot_time()
    }
    return jsonify(info)

@app.route('/list_drives', methods=['GET'])
def list_drives():
    drives = []
    bitmask = os.popen("fsutil fsinfo drives").read().split()[1:]
    for drive in bitmask:
        drives.append({
            'id': drive,
            'text': drive,
            'type': 'default',
            'children': True
        })
    return jsonify(drives)

@app.route('/list_directory', methods=['GET'])
def list_directory():
    path = request.args.get('path', 'D:\\')

    print(f"Listing directory for path: {path}")

    try:
        files = os.listdir(path)
        file_details = []
        for file in files:
            full_path = os.path.join(path, file)
            if os.path.isdir(full_path):
                file_details.append({
                    'id': full_path,
                    'text': file,
                    'type': 'default',
                    'children': True
                })
            else:
                file_details.append({
                    'id': full_path,
                    'text': file,
                    'type': 'file'
                })
        return jsonify(file_details)
    except Exception as e:
        print(f"Error listing directory: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Open the default web browser
    webbrowser.open('http://127.0.0.1:5000/')
    # Start the Flask server
    app.run(debug=True)
