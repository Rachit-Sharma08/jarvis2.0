"""Web search via SerpAPI (read-only)."""
import json
import os
import urllib.parse
import urllib.request

SERPAPI_KEY = os.getenv('SERPAPI_API_KEY', '').strip()


def web_search(query: str = '', num: int = 5) -> str:
    if not query or not str(query).strip():
        return 'Search query kya hai?'
    q = str(query).strip()
    if not SERPAPI_KEY:
        return 'SERPAPI_API_KEY .env me nahi hai.'
    try:
        n = max(1, min(int(num or 5), 10))
        params = {'q': q, 'api_key': SERPAPI_KEY, 'engine': 'google', 'num': str(n)}
        url = 'https://serpapi.com/search.json?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': 'Jarvis/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode('utf-8', errors='ignore'))
    except Exception as exc:
        return f'Search error: {type(exc).__name__}'
    res = []
    for i, r in enumerate(data.get('organic_results', [])[:n], 1):
        title = (r.get('title') or '')[:200]
        link = r.get('link') or ''
        snip = (r.get('snippet') or '')[:300]
        res.append(f'{i}. {title}\n{snip}\n{link}')
    return '\n\n'.join(res) if res else 'Koi result nahi mila'
