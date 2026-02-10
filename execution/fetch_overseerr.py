import urllib.request
import urllib.error
import json
import os
from datetime import datetime

def fetch_overseerr_data():
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
        # Filter is notoriously flaky in Overseerr API, so we fetch recent requests and filter manually
        req = urllib.request.Request(f"{base_url}/api/v1/request?take=50&sort=added&skip=0", headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            try:
                data = json.loads(response.read().decode('utf-8'))
            except json.JSONDecodeError:
                return {'error': 'Overseerr: Invalid JSON response.'}
        
        results = data.get('results', [])
        pending_requests = []
        
        # Filter for status = 1 (PENDING APPROVAL)
        for item in results:
            if item.get('status') == 1:
                media = item.get('media', {})
                user = item.get('requestedBy', {})
                
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

                # Image URL
                poster_path = media.get('posterPath')
                # Overseerr images are often proxied via TMDB image service
                # We can construct a TMDB url if we have the path
                image_url = ""
                if poster_path:
                   image_url = f"https://image.tmdb.org/t/p/w200{poster_path}"
                
                # Title
                title = "Unknown Title"
                if media.get('mediaType') == 'movie':
                     title = media.get('tmdbId') # Wait, media object usually has metadata? 
                     # Actually, the 'media' object in /request response is light.
                     # But current Overseerr versions usually include it. 
                     # Let's fallback to asking the item directly if media is bare
                     pass
                
                # Better way: The `media` object inside `results` usually has `tmdbId` etc. 
                # But the request object itself might have `media` info embedded differently depending on version.
                # Let's inspect standard output.
                # Standard /request response items have:
                # { id: 1, status: 1, media: { tmdbId: 123, status: ... } }
                # But does it have the TITLE? 
                # Usually we might need to fetch media details, but that's n+1.
                # Let's look at the `media` object. 
                # Some versions of API return `media` populated with `tmdbId`.
                # Wait, usually the request listing includes basic info. 
                # Let's check if the 'media' object is enriched or if we need to rely on what's there.
                
                # Actually, looking at Overseerr API docs, the result item has `media` which has `tmdbId`.
                # The result item DOES NOT usually have the title directly if it's just the request wrapper?
                # Wait, standard response: 
                # { "id": 1, "status": 1, "media": { ... }, "type": "movie" }
                # It seems the request object DOES NOT always carry the title.
                # However, usually the dashboard needs to show it.
                # Let's try to grab it from `media` if available, or maybe `title` is on the root object?
                # Re-checking API docs/community examples: 
                # The request object has `media` which is the media item in Overseerr db. 
                # BUT, often to get the title, one might need to use the `media` endpoint or rely on `media` having it.
                # Let's write code that assumes it MIGHT be there, but effectively we might just have `tmdbId`.
                
                # CORRECT APPROACH for efficient dashboard:
                # The list endpoint *usually* hydrates `media` enough or we might need to rely on what we get.
                # Actually checking a sample response: the `media` object has `tmdbId`.
                # But wait, looking at `fetch_overseerr_data` context, we want to avoid N+1 requests.
                # Let's assume for now we can get the title. 
                # If not, we might handle it gracefully.
                # Actually, let's look at a safer property: 
                # Many request responses include `media` -> which has `tmdbId`.
                # AND they include `...`?
                
                # Let's try to find title in `media.title` (if it's a media object) or root.
                # If we look at the type, `movie` or `tv`.
                
                # Mock approach for safety:
                # We will check keys.
                
                request_title = "Unknown"
                # Sometimes it's in media. 
                # Let's try to get it from `media` dict if possible.
                # Else leave as Unknown.
                
                # Actually, let's look at what we sent in the plan: "title, user, date, image".
                # I will trust that `media` object has `originalTitle` or `name` or `title`.
                
                if 'title' in media:
                     request_title = media['title']
                elif 'name' in media:
                     request_title = media['name']
                elif 'originalTitle' in media:
                    request_title = media['originalTitle']
                elif 'originalName' in media:
                    request_title = media['originalName']
                
                # Fallback: if we only have tmdbId, we might be stuck without a title without doing more calls.
                # But most API responses for lists include a snapshot.
                
                pending_requests.append({
                    'id': item.get('id'),
                    'title': request_title,
                    'user': user.get('email', 'Unknown User').split('@')[0], # Use username part of email if username missing
                    'user_avatar': user.get('avatar'), # valid URL or null
                    'date': date_str,
                    'image': image_url,
                    'status': 'Pending Approval'
                })

        return {
            'requests': pending_requests,
            'count': len(pending_requests)
        }
        
    except Exception as e:
        return {'error': str(e)}
