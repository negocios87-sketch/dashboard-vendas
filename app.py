import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

PIPEDRIVE_TOKEN    = os.environ.get('PIPEDRIVE_TOKEN')
PIPEDRIVE_ORG      = os.environ.get('PIPEDRIVE_ORG', 'boardacademy')
PIPEDRIVE_FILTER   = os.environ.get('PIPEDRIVE_FILTER_ID', '74674')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/deals')
def deals():
    if not PIPEDRIVE_TOKEN:
        return jsonify({'error': 'PIPEDRIVE_TOKEN não configurado'}), 500

    url = f'https://{PIPEDRIVE_ORG}.pipedrive.com/api/v1/deals'
    params = {
        'filter_id': PIPEDRIVE_FILTER,
        'status':    'won',
        'limit':     500,
        'start':     0,
        'api_token': PIPEDRIVE_TOKEN
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return jsonify(r.json().get('data') or [])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
