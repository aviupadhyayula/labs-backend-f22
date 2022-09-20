from flask import Blueprint, jsonify
from utils import jsonify_tags
from app import cache
from models import *

tag = Blueprint('tag', __name__, url_prefix='/api/tags')

@tag.route('/', methods=['GET'])
@cache.memoize(timeout=60)
def get_tags():
    tags = Tag.query.all()
    return jsonify_tags(tags), 200
