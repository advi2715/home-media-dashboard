import urllib.request
import urllib.error
import json
import os

def fetch_radarr_data():
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
        health_req = urllib.request.Request(f"{base_url}/api/v3/health", headers=headers)
        with urllib.request.urlopen(health_req, timeout=5) as response:
            try:
                health_data = json.loads(response.read().decode('utf-8'))
            except json.JSONDecodeError:
                return {'error': 'Radarr: Invalid JSON response. Check URL.'}
        
        errors = [h for h in health_data if h.get('type') == 'error']
        warnings = [h for h in health_data if h.get('type') == 'warning']
        
        # Queue
        queue_req = urllib.request.Request(f"{base_url}/api/v3/queue", headers=headers)
        with urllib.request.urlopen(queue_req, timeout=5) as response:
            try:
                queue_data = json.loads(response.read().decode('utf-8'))
            except json.JSONDecodeError:
                return {'error': 'Radarr: Invalid JSON response from Queue endpoint.'}
        
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
        
    except Exception as e:
        return {'error': str(e)}
