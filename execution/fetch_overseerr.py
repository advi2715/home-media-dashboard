import aiohttp
import asyncio
import json
import os
from datetime import datetime

async def fetch_overseerr_data(session):
    base_url = os.getenv('OVERSEERR_URL')
    api_key = os.getenv('OVERSEERR_API_KEY')
    
    if not base_url or not api_key:
        return {'error': 'Overseerr not configured'}

    base_url = base_url.rstrip('/')

    headers = {
        'X-Api-Key': api_key,
        'Accept': 'application/json'
    }
    
    try:
        # Fetch requests
        async with session.get(f"{base_url}/api/v1/request?take=50&sort=added&skip=0", headers=headers, timeout=2) as response:
             if response.status != 200:
                 return {'error': f'Overseerr HTTP {response.status}'}
             data = await response.json()
        
        results = data.get('results', [])
        pending_requests = []
        
        # Filter for status = 1 (PENDING APPROVAL)
        for item in results:
            if item.get('status') == 1:
                media = item.get('media') or {}
                user = item.get('requestedBy') or {}
                request_type = item.get('type') # 'movie' or 'tv'
                
                # Format date
                created_at = item.get('createdAt')
                date_str = "Unknown Date"
                if created_at:
                    try:
                        # created_at is an ISO string usually
                        dt = datetime.strptime(created_at.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        date_str = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass

                # Basic Info from list
                poster_path = media.get('posterPath')
                tmdb_id = media.get('tmdbId')
                
                title = "Unknown Title"
                # Try simple title from properties if they exist
                if 'title' in media:
                     title = media['title']
                elif 'name' in media:
                     title = media['name']
                elif 'originalTitle' in media:
                    title = media['originalTitle']
                elif 'originalName' in media:
                    title = media['originalName']
                
                # If title is still unknown or we want to ensure we have the poster, fetch details
                if (title == "Unknown Title" or not poster_path) and tmdb_id and request_type:
                    try:
                        # Fetch details from Overseerr (which proxies/caches TMDB)
                        # Ensure request_type matches endpoint expectation (movie/tv)
                        detail_url = f"{base_url}/api/v1/{request_type}/{tmdb_id}"
                        async with session.get(detail_url, headers=headers, timeout=3) as resp_d:
                            if resp_d.status == 200:
                                details = await resp_d.json()
                                
                                # Update title
                                if 'title' in details:
                                    title = details['title']
                                elif 'name' in details:
                                    title = details['name']
                                    
                                # Update poster if missing
                                if not poster_path and 'posterPath' in details:
                                    poster_path = details['posterPath']
                    except Exception as e:
                        # Fail silently on details fetch to avoid breaking the dashboard
                        print(f"Overseerr detail fetch failed for {tmdb_id}: {e}")

                # Image URL
                image_url = ""
                if poster_path:
                   image_url = f"https://image.tmdb.org/t/p/w200{poster_path}"
                
                pending_requests.append({
                    'id': item.get('id'),
                    'title': title,
                    'user': user.get('email', 'Unknown User').split('@')[0], 
                    'user_avatar': user.get('avatar'), 
                    'date': date_str,
                    'image': image_url,
                    'status': 'Pending Approval'
                })

        return {
            'requests': pending_requests,
            'count': len(pending_requests)
        }
        
    except asyncio.TimeoutError:
         return {'error': 'Overseerr Connection Timeout'}
    except aiohttp.ClientError as e:
         return {'error': f'Overseerr Connection Error: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}
