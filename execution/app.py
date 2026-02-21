from quart import Quart, render_template, jsonify, request
import asyncio
import aiohttp
import os
import sys
from dotenv import load_dotenv

from fetch_plex import fetch_plex_data
from fetch_qbittorrent import fetch_qbittorrent_data, delete_torrent
from fetch_sonarr import fetch_sonarr_data
from fetch_radarr import fetch_radarr_data
from fetch_overseerr import fetch_overseerr_data

load_dotenv()

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Quart(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Quart(__name__, static_folder='static', template_folder='templates')

# Shared aiohttp session
app.client_session = None

@app.before_serving
async def startup():
    app.client_session = aiohttp.ClientSession(
        cookie_jar=aiohttp.CookieJar(unsafe=True)
    )

@app.after_serving
async def shutdown():
    if app.client_session:
        await app.client_session.close()

@app.route('/')
async def index():
    return await render_template('index.html',
        plex_url=os.getenv('PLEX_URL', 'http://localhost:32400'),
        qbittorrent_url=os.getenv('QBITTORRENT_URL', 'http://localhost:8080'),
        sonarr_url=os.getenv('SONARR_URL', 'http://localhost:8989'),
        radarr_url=os.getenv('RADARR_URL', 'http://localhost:7878'),
        overseerr_url=os.getenv('OVERSEERR_URL', 'http://localhost:5055')
    )

@app.route('/api/data')
async def get_data():
    if not app.client_session:
        app.client_session = aiohttp.ClientSession()
        
    plex_task = fetch_plex_data(app.client_session)
    qbit_task = fetch_qbittorrent_data(app.client_session)
    sonarr_task = fetch_sonarr_data(app.client_session)
    radarr_task = fetch_radarr_data(app.client_session)
    overseerr_task = fetch_overseerr_data(app.client_session)
    
    # Run all fetches concurrently
    results = await asyncio.gather(plex_task, qbit_task, sonarr_task, radarr_task, overseerr_task, return_exceptions=True)
    
    # Unpack results, handling exceptions safely if any slipped through return_exceptions=True
    # (Though return_exceptions=True means results contains exceptions as objects)
    data = []
    for log, res in zip(['Plex', 'Qbit', 'Sonarr', 'Radarr', 'Overseerr'], results):
        if isinstance(res, Exception):
            print(f"Error fetching {log}: {res}")
            data.append({'error': str(res)})
        else:
            data.append(res)
            
    urls = {
        'plex': os.getenv('PLEX_URL', 'http://localhost:32400'),
        'qbittorrent': os.getenv('QBITTORRENT_URL', 'http://localhost:8080'),
        'sonarr': os.getenv('SONARR_URL', 'http://localhost:8989'),
        'radarr': os.getenv('RADARR_URL', 'http://localhost:7878'),
        'overseerr': os.getenv('OVERSEERR_URL', 'http://localhost:5055')
    }

    return jsonify({
        'plex': data[0],
        'qbittorrent': data[1],
        'sonarr': data[2],
        'radarr': data[3],
        'overseerr': data[4],
        'urls': urls
    })

@app.route('/api/delete_torrent', methods=['POST'])
async def delete_torrent_route():
    data = await request.get_json()
    t_hash = data.get('hash')
    delete_files = data.get('delete_files', False)
    
    if not t_hash:
        return jsonify({'error': 'No hash provided'}), 400
    
    if not app.client_session:
        app.client_session = aiohttp.ClientSession()
        
    result = await delete_torrent(app.client_session, t_hash, delete_files)
    return jsonify(result)

@app.route('/_next/<path:path>')
async def next_assets(path):
    return await app.send_static_file(f'_next/{path}')

@app.route('/favicon.ico')
async def favicon():
    return await app.send_static_file('favicon.ico')

@app.route('/<path:path>')
async def catch_all(path):
    # Try serving from root of static (e.g. 404.html, other assets)
    try:
        return await app.send_static_file(path)
    except Exception:
        return await app.send_static_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7152))
    # Quart run
    app.run(host='0.0.0.0', port=port, use_reloader=False)
