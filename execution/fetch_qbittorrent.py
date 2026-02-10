import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import os

def fetch_qbittorrent_data():
    base_url = os.getenv('QBITTORRENT_URL')
    username = os.getenv('QBITTORRENT_USERNAME')
    password = os.getenv('QBITTORRENT_PASSWORD')
    
    if not base_url:
        return {'error': 'Qbittorrent URL not configured'}

    # Setup Cookie Jar for authentication
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # Headers - qBittorrent sometimes likes a User-Agent, though not strictly required
    opener.addheaders = [('User-Agent', 'MediaDashboard/1.0')]

    try:
        # 1. Login
        if username and password:
            login_data = urllib.parse.urlencode({'username': username, 'password': password}).encode('utf-8')
            # Login is a POST request
            # qBittorrent returns 200 OK with "Ok." body on success, or 200 OK with "Fails." on failure (older versions)
            # or just sets the cookie.
            try:
                with opener.open(f"{base_url}/api/v2/auth/login", data=login_data, timeout=5) as login_resp:
                    login_text = login_resp.read().decode('utf-8')
                    if "Fails." in login_text: # Some versions return "Fails." text
                        return {'error': 'Qbittorrent Login Failed'}
            except urllib.error.HTTPError as e:
                 # If 401/403
                 return {'error': f"Login HTTP Error: {e.code}"}

        # 2. Get Torrents
        # API: /api/v2/torrents/info
        torrents_url = f"{base_url}/api/v2/torrents/info?sort=added_on&reverse=true&limit=20"
        with opener.open(torrents_url, timeout=5) as resp:
            torrents = json.loads(resp.read().decode('utf-8'))
        
        # Status mapping
        status_map = {
            'error': 'Error',
            'missingFiles': 'Missing Files',
            'uploading': 'Seeding',
            'pausedUP': 'Seeding',
            'queuedUP': 'Seeding',
            'stalledUP': 'Seeding',
            'checkingUP': 'Checking',
            'forcedUP': 'Seeding',
            'allocating': 'Allocating',
            'downloading': 'Downloading',
            'metaDL': 'Downloading',
            'pausedDL': 'Paused',
            'queuedDL': 'Queued',
            'stalledDL': 'Stalled',
            'checkingDL': 'Checking',
            'forcedDL': 'Downloading',
            'checkingResumeData': 'Checking',
            'moving': 'Moving'
        }

        recent_downloads = []
        for torrent in torrents:
            state = torrent.get('state', 'unknown')
            readable_state = status_map.get(state, state)
            
            # dlspeed is bytes/s
            dlspeed = torrent.get('dlspeed', 0)
            
            # progress is 0-1
            progress = torrent.get('progress', 0) * 100
            
            recent_downloads.append({
                'name': torrent.get('name'),
                'state': readable_state,
                'dlspeed': dlspeed,
                'progress': f"{progress:.1f}%"
            })

        # 3. Get Error Count
        # We limit the fetch to avoid memory issues (fixed previously), and now use urllib
        error_limit = 500
        error_url = f"{base_url}/api/v2/torrents/info?filter=error&limit={error_limit}"
        
        errored_torrents = []
        try:
            with opener.open(error_url, timeout=5) as error_resp:
                 errors_data = json.loads(error_resp.read().decode('utf-8'))
            
            for i, err in enumerate(errors_data):
                error_msg = 'Unknown Error'
                t_hash = err.get('hash')
                
                # Fetch trackers for this error to find the message
                # This could be slow for many errors, but we rely on the limit=500 and user pattern
                if t_hash:
                    try:
                        trackers_url = f"{base_url}/api/v2/torrents/trackers?hash={t_hash}"
                        with opener.open(trackers_url, timeout=5) as trackers_resp:
                            trackers = json.loads(trackers_resp.read().decode('utf-8'))
                            # Find first tracker with message
                            for tracker in trackers:
                                msg = tracker.get('msg', '')
                                # Ignore common non-error messages or informational flags
                                if not msg or "this torrent is private" in msg.lower() or msg.lower() == "ok":
                                    continue
                                
                                error_msg = msg
                                break
                    except Exception:
                        pass # Ignore tracker fetch failures
                
                # If the error message was ignored (still 'Unknown Error') and the state is not a hard error state, 
                # assume it's a false positive from filter=error (e.g. tracker warning on private torrent)
                # Hard error states: error, missingFiles
                state = err.get('state', 'unknown')
                if error_msg == 'Unknown Error' and state not in ['error', 'missingFiles', 'metaDL']:
                    continue

                errored_torrents.append({
                    'name': err.get('name'),
                    'hash': err.get('hash'),
                    'state': state,
                    'message': error_msg
                })
        
        except Exception:
            pass

        # 4. Get Global Transfer Info
        # API: /api/v2/transfer/info
        transfer_info = {}
        try:
            with opener.open(f"{base_url}/api/v2/transfer/info", timeout=5) as transfer_resp:
                t_data = json.loads(transfer_resp.read().decode('utf-8'))
                transfer_info = {
                    'dl_info_data': t_data.get('dl_info_data', 0),
                    'up_info_data': t_data.get('up_info_data', 0),
                    'dl_info_speed': t_data.get('dl_info_speed', 0),
                    'up_info_speed': t_data.get('up_info_speed', 0)
                }
        except Exception:
             # If this fails, we just don't show the global stats, not critical enough to fail everything
            pass

        return {
            'recent': recent_downloads,
            'active_downloads': [t for t in recent_downloads if t['state'] == 'Downloading'],
            'error_count': len(errored_torrents),
            'errored_torrents': errored_torrents,
            'transfer_info': transfer_info
        }

    except Exception as e:
        return {'error': str(e)}

def delete_torrent(torrent_hash, delete_files=False):
    base_url = os.getenv('QBITTORRENT_URL')
    username = os.getenv('QBITTORRENT_USERNAME')
    password = os.getenv('QBITTORRENT_PASSWORD')
    
    if not base_url:
        return {'error': 'Qbittorrent URL not configured'}

    # Setup Cookie Jar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'MediaDashboard/1.0')]
    
    try:
        # Login
        if username and password:
            login_data = urllib.parse.urlencode({'username': username, 'password': password}).encode('utf-8')
            with opener.open(f"{base_url}/api/v2/auth/login", data=login_data, timeout=5) as login_resp:
                pass # Check success?

        # Delete torrent
        delete_url = f"{base_url}/api/v2/torrents/delete"
        post_data = urllib.parse.urlencode({
            'hashes': torrent_hash,
            'deleteFiles': 'true' if delete_files else 'false'
        }).encode('utf-8')
        
        with opener.open(delete_url, data=post_data, timeout=5) as resp:
            # 200 OK usually
            pass
        
        return {'success': True}

    except Exception as e:
        return {'error': str(e)}
