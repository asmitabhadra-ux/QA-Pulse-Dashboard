import pytest

@pytest.fixture(scope="session")
def base_url():
    return "https://www.saucedemo.com"

@pytest.fixture(scope="session")
def valid_credentials():
    return {"username": "standard_user", "password": "secret_sauce"}

@pytest.fixture(scope="session")
def locked_credentials():
    return {"username": "locked_out_user", "password": "secret_sauce"}
