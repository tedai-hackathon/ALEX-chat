import pytest


@pytest.fixture(scope="session")
def urls():
    return [
        "https://apple.com",
    ]
