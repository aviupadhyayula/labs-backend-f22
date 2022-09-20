from flask import Blueprint, jsonify, request
from app import db, token_required, cache
from models import *
from utils import *

favorite = Blueprint('favorite', __name__, url_prefix='/api/favorites')

@favorite.route('/', methods=['GET'])
@cache.memoize(timeout=600)
@token_required
def get_favorites(current_user):
    clubs = [club for club in current_user.favorites]
    return jsonify_clubs(clubs), 200
    
@favorite.route('/', methods=['POST'])
@token_required
def add_favorite(current_user):
    data = request.get_json()
    if 'code' not in data:
        return make_response(False, 'Club code missing in request.', 400)
    code = data['code']
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    current_user.favorites.append(club)
    db.session.commit()
    cache.delete_memoized(get_favorites)
    return make_response(True, "Added to favorites.", 201)

@favorite.route('/<code>', methods=['DELETE'])
@token_required
def remove_favorite(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'no such club found', 404)
    if club not in current_user.favorites:
        return make_response(False, 'no such club favorited', 404)
    current_user.favorites.remove(club)
    db.session.commit()
    cache.delete_memoized(get_favorites)
    return make_response(True, 'favorite removed', 200)
