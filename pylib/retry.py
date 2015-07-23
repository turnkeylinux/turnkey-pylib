"""
Usage:

    @retry(3)
    @retry(3, backoff=2)

Gotcha:

    Backoff is exponential

"""
from time import sleep

def retry(retries, delay=1, backoff=1):
    """
    Argument:

        retries     how many times to retry if exception is raised
        delay       how many seconds to delay in case of failure
        backoff     exponential delay backoff factor
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            mydelay = delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except:
                    mydelay *= backoff
                    if mydelay:
                        sleep(mydelay)
            else:
                raise

        return wrapper
    return decorator

