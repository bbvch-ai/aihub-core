import asyncio
import functools

import pytest


def async_test(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return asyncio.run(func(*args, **kwargs))
        except Exception as e:
            pytest.fail(f"Failed due to exception: {str(e)}")
            return None

    return wrapper
