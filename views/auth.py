from flask import Blueprint, request, redirect, jsonify
from app import db, token_required
from models import *
from utils import *
import bcrypt

auth = Blueprint('auth', __name__, url_prefix='/api/')

@auth.route('signup', methods=['POST'])
def signup():
    data = request.get_json()
    required = ['username', 'email', 'password']
    if not all(item in data for item in required):
        return make_response(False, 'Missing credentials.', 400)
    username = data['username'].lower()
    email = data['email'].lower()
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return make_response(False, 'User with username and/or email already exists.', 409)
    password = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect('login', code=201)

@auth.route('login', methods=['POST'])
def login():
    data = request.get_json()
    required = ['username', 'password']
    if not all(item in data for item in required):
        return make_response(False, 'Missing credentials.', 400)
    username = data['username']
    password = data['password'].encode('utf-8')
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password, user.password):
        return make_response(False, 'Invalid authentication credentials.', 401)
    token = create_token(username)
    responseObject = {
        'status': 'success',
        'message': 'Successfully logged in.',
        'auth_token': token
    }
    return jsonify(responseObject), 200

@auth.route('logout', methods=['POST'])
@token_required
def logout(user):
    token = request.headers.get('auth_token')
    invalidate_token(token)
    return make_response(True, 'Logged out.', 200)
