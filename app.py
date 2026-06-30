import os
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

PIPEDRIVE_TOKEN  = os.environ.get('PIPEDRIVE_TOKEN')
PIPEDRIVE_ORG    = os.environ.get('PIPEDRIVE_ORG', 'boardacademy')
PIPEDRIVE_FILTER = os.environ.get('PIPEDRIVE_FILTER_ID', '1464384')

_pipelines_cache = None

def fetch_pipelines():
    """Busca a lista de pipelines (funis) e monta um dict {id: nome}.
    Cacheado em memória pra não bater na API toda hora."""
    global _pipelines_cache
    if _pipelines_cache is not None:
        return _pipelines_cache
    url = f'https://{PIPEDRIVE_ORG}.pipedrive.com/api/v1/pipelines'
    r = requests.get(url, params={'api_token': PIPEDRIVE_TOKEN}, timeout=15)
    r.raise_for_status()
    data = r.json().get('data') or []
    _pipelines_cache = {p['id']: p['name'] for p in data}
    return _pipelines_cache

def fetch_deals():
    url = f'https://{PIPEDRIVE_ORG}.pipedrive.com/api/v1/deals'
    params = {
        'filter_id': PIPEDRIVE_FILTER,
        'status':    'won',
        'limit':     500,
        'start':     0,
        'sort':      'won_time DESC',
        'api_token': PIPEDRIVE_TOKEN
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    deals = r.json().get('data') or []

    # Anexa o nome do funil em cada deal
    pipelines = fetch_pipelines()
    for d in deals:
        pid = d.get('pipeline_id')
        d['pipeline_name'] = pipelines.get(pid, None)

    return deals

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/deals')
def deals():
    if not PIPEDRIVE_TOKEN:
        return jsonify({'error': 'PIPEDRIVE_TOKEN não configurado'}), 500
    return jsonify(fetch_deals())

@app.route('/api/pipelines')
def pipelines():
    if not PIPEDRIVE_TOKEN:
        return jsonify({'error': 'PIPEDRIVE_TOKEN não configurado'}), 500
    return jsonify(fetch_pipelines())

@app.route('/api/debug')
def debug():
    if not PIPEDRIVE_TOKEN:
        return jsonify({'error': 'PIPEDRIVE_TOKEN não configurado'}), 500
    from datetime import datetime
    now    = datetime.now()
    mes_ym = f"{now.year}-{str(now.month).zfill(2)}"
    todos  = fetch_deals()
    do_mes = [d for d in todos if (d.get('won_time') or '').startswith(mes_ym)]
    return jsonify({
        'mes_filtrado':   mes_ym,
        'total_deals':    len(todos),
        'deals_do_mes':   len(do_mes),
        'nomes_no_mes':   list(set(d['user_id']['name'] for d in do_mes if d.get('user_id'))),
        'pipelines_no_mes': list(set(d.get('pipeline_name') for d in do_mes if d.get('pipeline_name'))),
        'won_times_top5': [d.get('won_time') for d in todos[:5]]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
