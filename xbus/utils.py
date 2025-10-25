import asyncio
import functools


def async_cache(maxsize=128):
    cache = {}
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = functools._make_key(args, kwargs, typed=False)
            if key not in cache:
                if len(cache) >= maxsize:
                    del cache[next(iter(cache))]
                future = asyncio.Future()
                cache[key] = future
                try:
                    future.set_result(await func(*args, **kwargs))
                except Exception as e:
                    future.set_exception(e)
                    del cache[key]
                    raise
            return await cache[key]
        return wrapper
    return decorator
