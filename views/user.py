from flask import Blueprint, jsonify, abort, request
from app import db, token_required
from models import *
from utils import *

user = Blueprint('user', __name__, url_prefix='/api/users')

@user.route('/<username>', methods=['GET'])
@token_required
def get_user(current_user, username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return make_response(False, 'No user with this username found.', 400)
    return jsonify(user.to_dict()), 200

@user.route('/<username>', methods=['PUT'])
@token_required
def modify_user(current_user, username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return make_response(False, 'No user with this username found.', 404)
    if user != current_user:
        return make_response(False, 'You can only edit your own user information.', 403)
    data = request.get_json()
    if 'username' not in data:
        return make_response(False, 'Matching username not found in request.', 400)
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        import bcrypt
        new_password = data['password'].encode('utf8')
        user.password = bcrypt.hashpw(new_password, bcrypt.gensalt())
    db.session.commit()
    return make_response(True, 'User information successfully updated.', 201)

@user.route('/<username>', methods=['DELETE'])
@token_required
def delete_user(current_user, username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return make_response(False, 'No user with that username found.', 404)
    if user != current_user:
        return make_response(False, 'You can only delete your own user profile.', 403)
    invalidate_token(request.headers.get('auth_token'))
    db.session.delete(current_user)
    db.session.commit()
    return make_response(True, 'User successfully deleted.', 200)
