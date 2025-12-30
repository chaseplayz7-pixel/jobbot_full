import random
from typing import Optional, Dict
from urllib.parse import urlparse

def load_proxies(path: str = 'proxies.txt'):
    proxies = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if not line or line.startswith('#'):
                    continue
                proxies.append(line)
    except FileNotFoundError:
        return []
    return proxies

def pick_proxy(proxies: list) -> Optional[Dict]:
    if not proxies:
        return None
    p = random.choice(proxies)
    # p can be http://user:pass@host:port or host:port
    if '://' not in p:
        p = 'http://' + p
    parsed = urlparse(p)
    server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    cred = None
    if parsed.username:
        cred = {'username': parsed.username, 'password': parsed.password}
    return {'server': server, **(cred or {})}
