# /backend/app/services/cache.py
import time

_cache = {}

def set_cache(key, value, ttl=3600):
    _cache[key] = {"value": value, "expires": time.time() + ttl}

def get_cache(key):
    data = _cache.get(key)
    if not data:
        return None
    if time.time() > data["expires"]:
        del _cache[key]
        return None
    return data["value"]
