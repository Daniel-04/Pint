import time
import functools


def retry(func=None, *, num_tries=3, timeout=5, exceptions=(Exception,)):
    def deco(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            last_e = None
            for _ in range(num_tries):
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    last_e = e
                    time.sleep(timeout)
            raise last_e

        return wrap

    if func is None:
        return deco
    else:
        return deco(func)
