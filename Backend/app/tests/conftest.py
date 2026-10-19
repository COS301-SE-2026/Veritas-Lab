import pytest

from app.auth.auth import limiter


@pytest.fixture(autouse=True)
def disable_rate_limiting_for_tests():
    previous_state = limiter.enabled
    limiter.enabled = False
    try:
        yield
    finally:
        limiter.enabled = previous_state
