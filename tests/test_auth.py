import pytest

from app import app, db, DB_FILE
db.drop_all()
db.create_all()
client = app.test_client()

def test_signup():
    request = {
        'username': 'josh',
        'password': 'password',
        'email': 'josh@seas.upenn.edu'
    }
    response = client.post('/api/signup', json=request)
    assert response.status_code == 201

def test_signup_duplicate():
    request = {
        'username': 'josh',
        'password': 'password',
        'email': 'josh@seas.upenn.edu'
    }
    response = client.post('/api/signup', json=request)
    assert response.status_code == 409

def test_signup_missing_info():
    request = {
        'username': 'josh',
        'password': 'password',
    }
    response = client.post('/api/signup', json=request)
    assert response.status_code == 400

def test_login():
    request = {
        'username': 'josh',
        'password': 'password'
    }
    response = client.post('/api/login', json=request)
    assert response.status_code == 200

def test_login_wrong_info():
    request = {
        'username': 'josh',
        'password': '1234'
    }
    response = client.post('/api/login', json=request)
    assert response.status_code == 401

def test_logout():
    request = {
        'username': 'josh',
        'password': 'password'
    }
    response = client.post('/api/login', json=request)
    data = response.get_json()
    auth_token = data['auth_token']
    response = client.post('/api/logout', headers={'auth_token': auth_token})
    assert response.status_code == 200
    response = client.post('/api/logout', headers={'auth_token': auth_token})
    assert response.status_code == 401
