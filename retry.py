import math
import time
import functools


def retry(
    func=None, *, num_tries=None, timeout=2, max_timeout=3600, exceptions=(Exception,)
):
    def deco(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            if num_tries is None:
                tries = math.ceil(math.log(max_timeout / timeout, 2)) + 1
            else:
                tries = num_tries
            delay = timeout
            last_e = None

            for _ in range(tries):
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    print(
                        f"In function {f} caught exception {e}, retrying in {delay} seconds."
                    )
                    last_e = e
                    time.sleep(delay)
                    delay = min(delay * 2, max_timeout)
            raise last_e

        return wrap

    if func is None:
        return deco
    else:
        return deco(func)
