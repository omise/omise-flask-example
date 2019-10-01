import pytest
from config import Config
from app import create_app


class TestConfig(Config):
    TESTING = True


@pytest.fixture
def client(request):
    app = create_app(TestConfig)
    client = app.test_client()
    yield client


def test_index(client):
    """index works"""
    with client.session_transaction() as session:
        session["cart"] = ["nuts.jpg"]
    response = client.get("/")
    assert 200 == response.status_code


def test_checkout(client):
    """index works"""
    with client.session_transaction() as session:
        session["cart"] = ["nuts.jpg"]
    response = client.get("/checkout")
    assert 200 == response.status_code
