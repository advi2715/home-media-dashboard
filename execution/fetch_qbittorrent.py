import aiohttp
import asyncio
import urllib.parse
import json
import os

async def fetch_qbittorrent_data(session):
    base_url = os.getenv('QBITTORRENT_URL')
    username = os.getenv('QBITTORRENT_USERNAME')
    password = os.getenv('QBITTORRENT_PASSWORD')
    
    if not base_url:
        return {'error': 'Qbittorrent URL not configured'}

    base_url = base_url.rstrip('/')
    
    # We use the shared session, but qBittorrent needs cookies for auth.
    # aiohttp ClientSession handles cookies automatically if we reuse it.
    # However, if 'session' is shared across different services (Plex, Sonarr), 
    # we need to ensure we don't leak cookies or conflicts?
    # Actually, aiohttp session cookie jar is shared. qBit sets a cookie 'SID'. 
    # It shouldn't conflict with others usually (Plex uses headers, Arrs use headers).
    # BUT, if we want to be safe or if the passed session doesn't persist cookies correctly for this flow:
    # We might want to just login every time or rely on the session.
    # Let's assume the passed 'session' is a fresh one specific to the request or a global one.
    # If it's a global one, we should be fine. If it's per-request, we login once.
    
    headers = {'User-Agent': 'MediaDashboard/1.0'}

    try:
        # 1. Login
        if username and password:
            login_data = {'username': username, 'password': password}
            # Login
            async with session.post(f"{base_url}/api/v2/auth/login", data=login_data, headers=headers, timeout=5) as login_resp:
                if login_resp.status != 200:
                     return {'error': f'Qbittorrent Login HTTP {login_resp.status}'}
                text = await login_resp.text()
                if "Fails." in text:
                    return {'error': 'Qbittorrent Login Failed'}

        # 2. Get Torrents
        async with session.get(f"{base_url}/api/v2/torrents/info?sort=added_on&reverse=true&limit=20", headers=headers, timeout=5) as resp:
            if resp.status != 200:
                return {'error': f'Qbittorrent Info HTTP {resp.status}'}
            torrents = await resp.json()
        
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
            dlspeed = torrent.get('dlspeed', 0)
            progress = torrent.get('progress', 0) * 100
            
            recent_downloads.append({
                'name': torrent.get('name'),
                'state': readable_state,
                'dlspeed': dlspeed,
                'progress': f"{progress:.1f}%"
            })

        # 3. Get Error Count
        error_limit = 500
        errored_torrents = []
        try:
            async with session.get(f"{base_url}/api/v2/torrents/info?filter=error&limit={error_limit}", headers=headers, timeout=5) as error_resp:
                 if error_resp.status == 200:
                    errors_data = await error_resp.json()
                    
                    for err in errors_data:
                        error_msg = 'Unknown Error'
                        t_hash = err.get('hash')
                        
                        if t_hash:
                            try:
                                async with session.get(f"{base_url}/api/v2/torrents/trackers?hash={t_hash}", headers=headers, timeout=5) as trackers_resp:
                                    if trackers_resp.status == 200:
                                        trackers = await trackers_resp.json()
                                        for tracker in trackers:
                                            msg = tracker.get('msg', '')
                                            if not msg or "this torrent is private" in msg.lower() or msg.lower() == "ok":
                                                continue
                                            error_msg = msg
                                            break
                            except Exception:
                                pass 
                        
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
        transfer_info = {}
        try:
            async with session.get(f"{base_url}/api/v2/transfer/info", headers=headers, timeout=5) as transfer_resp:
                if transfer_resp.status == 200:
                    t_data = await transfer_resp.json()
                    transfer_info = {
                        'dl_info_data': t_data.get('dl_info_data', 0),
                        'up_info_data': t_data.get('up_info_data', 0),
                        'dl_info_speed': t_data.get('dl_info_speed', 0),
                        'up_info_speed': t_data.get('up_info_speed', 0)
                    }
        except Exception:
            pass

        return {
            'recent': recent_downloads,
            'active_downloads': [t for t in recent_downloads if t['state'] == 'Downloading'],
            'error_count': len(errored_torrents),
            'errored_torrents': errored_torrents,
            'transfer_info': transfer_info
        }

    except asyncio.TimeoutError:
         return {'error': 'Qbittorrent Connection Timeout'}
    except aiohttp.ClientError as e:
         return {'error': f'Qbittorrent Connection Error: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}

async def delete_torrent(session, torrent_hash, delete_files=False):
    base_url = os.getenv('QBITTORRENT_URL')
    username = os.getenv('QBITTORRENT_USERNAME')
    password = os.getenv('QBITTORRENT_PASSWORD')
    
    if not base_url:
        return {'error': 'Qbittorrent URL not configured'}

    base_url = base_url.rstrip('/')
    headers = {'User-Agent': 'MediaDashboard/1.0'}
    
    try:
        # Login (if session not already authenticated - strictly we should ensure auth)
        if username and password:
             login_data = {'username': username, 'password': password}
             async with session.post(f"{base_url}/api/v2/auth/login", data=login_data, headers=headers, timeout=5) as login_resp:
                if login_resp.status != 200:
                      return {'error': 'Qbittorrent login failed'}

        # Delete
        post_data = {
            'hashes': torrent_hash,
            'deleteFiles': 'true' if delete_files else 'false'
        }
        
        async with session.post(f"{base_url}/api/v2/torrents/delete", data=post_data, headers=headers, timeout=5) as resp:
             if resp.status != 200:
                 return {'error': f'Delete failed with HTTP {resp.status}'}
        
        return {'success': True}

    except Exception as e:
        return {'error': str(e)}
