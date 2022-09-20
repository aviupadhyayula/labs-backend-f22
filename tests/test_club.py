import pytest

from app import app, db, DB_FILE
db.drop_all()
db.create_all()
client = app.test_client()

import scraper
scraper.main()

def get_auth_token():
    request = {
        'username': 'aviu',
        'password': 'password',
        'email': 'aviu@seas.upenn.edu'
    }
    client.post('/api/signup', json=request)
    response = client.post('/api/login', json=request)
    data = response.get_json()
    auth_token = data['auth_token']
    return auth_token

AUTH_TOKEN = get_auth_token()

def test_get_clubs():
    response = client.get('/api/clubs/')
    data = response.get_json()
    assert len(data) == 200

def test_get_clubs_search():
    response = client.get('/api/clubs/', query_string={'search': 'wharton'})
    data = response.get_json()
    assert len(data) == 47

def test_add_club():
    request = {
        'name': 'Penn Labs',
        'tags': [
            {
                'name': 'Pre-Professional'
            }
        ]
    }
    response = client.post('/api/clubs/', json=request)
    assert response.status_code == 401
    prev_count = len(client.get('/api/clubs/').get_json())
    response = client.post('/api/clubs/', json=request, headers={'auth_token': AUTH_TOKEN})
    assert response.status_code == 201
    response = client.get('/api/clubs/')
    assert len(response.get_json()) == prev_count + 1

def test_get_club():
    response = client.get('/api/clubs/testing/')
    assert response.status_code == 404
    response = client.get('/api/clubs/penn-labs/')
    assert response.status_code == 200

def test_modify_club():
    request = {
        'name': 'Penn Laboratories',
        'code': 'penn-labs'
    }
    response = client.put('/api/clubs/penn-labs/', json=request, headers={'auth_token': AUTH_TOKEN})
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Penn Laboratories'

def test_get_club_members():
    response = client.get('/api/clubs/penn-labs/members/')
    data = response.get_json()
    assert len(data) == 1

def test_add_club_member():
    request = {
        'username': 'aviu'
    }
    response = client.post('/api/clubs/penn-labs/members/', json=request, headers={'auth_token': AUTH_TOKEN})
    assert response.status_code == 409
    response = client.get('/api/clubs/penn-labs/members/')
    data = response.get_json()
    assert len(data) == 1

def test_delete_club_owner():
    response = client.delete('/api/clubs/penn-labs/members/aviu', headers={'auth_token': AUTH_TOKEN})
    assert response.status_code == 409
    response = client.get('/api/clubs/penn-labs/members/')
    data = response.get_json()
    assert len(data) == 1

def test_delete_club():
    prev_count = len(client.get('/api/clubs/').get_json())
    response = client.delete('/api/clubs/penn-labs/', headers={'auth_token': AUTH_TOKEN})
    assert response.status_code == 200
    response = client.get('/api/clubs/').get_json()
    assert len(response) == prev_count - 1   
