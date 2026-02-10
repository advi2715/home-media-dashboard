from flask import Flask, render_template, jsonify
from fetch_plex import fetch_plex_data
from fetch_qbittorrent import fetch_qbittorrent_data
from fetch_sonarr import fetch_sonarr_data
from fetch_radarr import fetch_radarr_data
from fetch_overseerr import fetch_overseerr_data
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
        plex_url=os.getenv('PLEX_URL', 'http://localhost:32400'),
        qbittorrent_url=os.getenv('QBITTORRENT_URL', 'http://localhost:8080'),
        sonarr_url=os.getenv('SONARR_URL', 'http://localhost:8989'),
        radarr_url=os.getenv('RADARR_URL', 'http://localhost:7878'),
        overseerr_url=os.getenv('OVERSEERR_URL', 'http://localhost:5055')
    )

@app.route('/api/data')
def get_data():
    plex_data = fetch_plex_data()
    qbit_data = fetch_qbittorrent_data()
    sonarr_data = fetch_sonarr_data()
    radarr_data = fetch_radarr_data()
    overseerr_data = fetch_overseerr_data()
    
    return jsonify({
        'plex': plex_data,
        'qbittorrent': qbit_data,
        'sonarr': sonarr_data,
        'radarr': radarr_data,
        'overseerr': overseerr_data
    })

@app.route('/api/delete_torrent', methods=['POST'])
def delete_torrent_route():
    from fetch_qbittorrent import delete_torrent
    from flask import request
    
    data = request.json
    t_hash = data.get('hash')
    delete_files = data.get('delete_files', False)
    
    if not t_hash:
        return jsonify({'error': 'No hash provided'}), 400
        
    result = delete_torrent(t_hash, delete_files)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7152))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
