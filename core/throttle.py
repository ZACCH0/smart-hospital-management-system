from django.core.cache import cache


def _cache_key(scope, ip):
    return f'shms:throttle:{scope}:{ip}'


def check_rate_limit(scope, ip, limit, window):
    """
    Fixed-window counter stored in the shared cache.

    Returns (allowed, current_count). A cache failure never blocks a request:
    availability of the hospital app wins over a throttling miss.
    """
    key = _cache_key(scope, ip)
    try:
        if cache.add(key, 1, timeout=window):
            return True, 1
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=window)
            return True, 1
        return count <= limit, count
    except Exception:
        return True, 0


def reset_rate_limit(scope, ip):
    try:
        cache.delete(_cache_key(scope, ip))
    except Exception:
        pass
