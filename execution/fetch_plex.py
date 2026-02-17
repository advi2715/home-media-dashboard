import aiohttp
import asyncio
import urllib.parse
import json
import os
import traceback

async def fetch_plex_data(session):
    plex_url = os.getenv('PLEX_URL')
    plex_token = os.getenv('PLEX_TOKEN')
    
    if not plex_url or not plex_token:
        return {'error': 'Plex not configured'}

    plex_url = plex_url.rstrip('/')

    headers = {
        'Accept': 'application/json'
    }
    
    async def get_recent_items(lib_type, limit=5):
        # type 1 = Movie, type 4 = Episode
        params = urllib.parse.urlencode({
            'type': lib_type,
            'sort': 'addedAt:desc',
            'limit': limit,
            'X-Plex-Token': plex_token
        })
        
        try:
            url = f"{plex_url}/library/all?{params}"
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                     return {'error': f'Plex HTTP {response.status}'}
                data = await response.json()
            
            items = []
            if 'MediaContainer' in data and 'Metadata' in data['MediaContainer']:
                for item in data['MediaContainer']['Metadata']:
                    title = item.get('title')
                    if lib_type == 4: # Shows
                        grandparent = item.get('grandparentTitle', '')
                        parent = item.get('parentTitle', '') # Season
                        # Plex often puts show title in grandparentTitle for episodes
                        if grandparent:
                            title = f"{grandparent}" 
                        
                        # Use series poster (grandparentThumb) if available, else fallback to episode thumb
                        thumb_path = item.get('grandparentThumb') or item.get('thumb')
                        
                        items.append({
                            'title': title,
                            'episode': item.get('title'), # Episode name
                            'thumb': f"{plex_url}{thumb_path}?X-Plex-Token={plex_token}" if thumb_path else None
                        })
                    else:
                        items.append({
                            'title': title,
                            'year': item.get('year'),
                            'thumb': f"{plex_url}{item.get('thumb')}?X-Plex-Token={plex_token}" if item.get('thumb') else None
                        })
            return items
        except asyncio.TimeoutError:
            return {'error': 'Plex Connection Timeout'}
        except aiohttp.ClientError as e:
            return {'error': f'Plex Connection Error: {str(e)}'}
        except Exception as e:
            return {'error': f'Plex: {str(e)}'}

    async def get_latest_session():
        try:
            url = f"{plex_url}/status/sessions"
            req_headers = {**headers, 'X-Plex-Token': plex_token}
            async with session.get(url, headers=req_headers, timeout=5) as response:
                 if response.status != 200:
                     return []
                 data = await response.json()
            
            if 'MediaContainer' in data and data['MediaContainer'].get('size', 0) > 0:
                sessions = []
                metadata = data['MediaContainer'].get('Metadata', [])
                for item in metadata:
                    user = item.get('User', {}).get('title', 'Unknown User')
                    user_thumb = item.get('User', {}).get('thumb')
                    if user_thumb:
                        user_thumb = f"{user_thumb}?X-Plex-Token={plex_token}" 
                    
                    title = item.get('title')
                    # If episode
                    if item.get('type') == 'episode':
                        grandparent = item.get('grandparentTitle')
                        if grandparent:
                            title = f"{grandparent} - {title}"
                    
                    thumb = item.get('thumb')
                    if thumb:
                        thumb = f"{plex_url}{thumb}?X-Plex-Token={plex_token}"

                    sessions.append({
                        'user': user,
                        'user_thumb': user_thumb,
                        'title': title,
                        'thumb': thumb,
                        'year': item.get('year'),
                        'type': item.get('type')
                    })
                return sessions
            return []
        except Exception:
            return []

    try:
        # We can run these in parallel too if we wanted, but for now sequential inside the plex fetch is fine
        # explicitly enabling parallel here too
        results = await asyncio.gather(
            get_recent_items(1),
            get_recent_items(4),
            get_latest_session(),
            return_exceptions=True
        )

        recent_movies = results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])}
        recent_shows = results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])}
        active_sessions = results[2] if not isinstance(results[2], Exception) else []

        # Error bubbling remains similar logic
        if isinstance(recent_movies, dict) and 'error' in recent_movies:
             # Just return it to show the error on the card
             pass 

        return {
            'movies': recent_movies,
            'shows': recent_shows,
            'active_sessions': active_sessions
        }
    except Exception as e:
        return {'error': str(e)}
