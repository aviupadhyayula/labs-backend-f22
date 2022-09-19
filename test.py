import pytest
import bootstrap
from app import app, db, DB_FILE
from models import *
import json

TEST_AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODU2NjU5NDgsImlhdCI6MTY2MzU0NzU0OCwic3ViIjoiam9zaCJ9.d5tD_PjmmD7is46rtOQuvGSWxF7HLKsjK5Vnqwjwhsc'
headers = {'auth_token': TEST_AUTH_TOKEN}

SAMPLE_TAGS = [{'name': 'Pre-Professional'}, {'name': 'Social'}]

@pytest.fixture
def app():
    from app import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['DEBUG'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
    db.drop_all()
    db.create_all()
    bootstrap.create_user()
    bootstrap.load_data()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_clubs(client):
    response = client.get('/api/clubs/')
    data = json.loads(response.data)
    assert len(data) == 205

def test_get_clubs_search(client):
    response = client.get('/api/clubs/?search=nursing')
    data = json.loads(response.data)
    assert len(data) == 40


