import logging
import time

logger = logging.getLogger(__name__)

def timed(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)   # capture return value
        end = time.perf_counter()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result   # return it back
    return wrapper