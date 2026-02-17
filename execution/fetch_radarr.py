import aiohttp
import asyncio
import json
import os

async def fetch_radarr_data(session):
    base_url = os.getenv('RADARR_URL')
    api_key = os.getenv('RADARR_API_KEY')
    
    if not base_url or not api_key:
        return {'error': 'Radarr not configured'}

    base_url = base_url.rstrip('/')

    headers = {
        'X-Api-Key': api_key,
        'Accept': 'application/json'
    }
    
    try:
        # System Status (Health)
        async with session.get(f"{base_url}/api/v3/health", headers=headers, timeout=5) as health_resp:
            if health_resp.status != 200:
                return {'error': f'Radarr Health HTTP {health_resp.status}'}
            health_data = await health_resp.json()
        
        errors = [h for h in health_data if h.get('type') == 'error']
        warnings = [h for h in health_data if h.get('type') == 'warning']
        
        # Queue
        async with session.get(f"{base_url}/api/v3/queue", headers=headers, timeout=5) as queue_resp:
             if queue_resp.status != 200:
                return {'error': f'Radarr Queue HTTP {queue_resp.status}'}
             queue_data = await queue_resp.json()
        
        records = queue_data.get('records', [])
        activity = []
        for item in records:
            activity.append({
                'title': item.get('title'),
                'status': item.get('status'),
                'protocol': item.get('protocol')
            })

        return {
            'errors': errors,
            'warnings': warnings,
            'activity': activity
        }
        
    except asyncio.TimeoutError:
         return {'error': 'Radarr Connection Timeout'}
    except aiohttp.ClientError as e:
         return {'error': f'Radarr Connection Error: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}
