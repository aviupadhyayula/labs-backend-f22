from flask import Blueprint, jsonify, abort, request
from app import db, token_required, cache
from models import *
from utils import *
import os

club = Blueprint('club', __name__, url_prefix='/api/clubs')

@club.route('/', methods=['GET'])
@cache.memoize(timeout=600)
def get_clubs():
    clubs = Club.query.all()
    if request.args.get('search'):
        search = '%{}%'.format(request.args.get('search'))
        clubs = Club.query.filter(Club.name.like(search)).all()
    return jsonify_clubs(clubs), 200

@club.route('/', methods=['POST'])
@token_required
def add_club(current_user):
    data = request.get_json()
    if 'name' not in data or 'tags' not in data:
        return make_response(False, 'Name or tags missing.', 400)
    name = data['name']
    tags = [tag['name'] for tag in data['tags']]
    code = create_club_code(name)
    if 'code' in data:
        code = create_club_code(data['code'])
    if Club.query.filter_by(code=code).first() or Club.query.filter_by(name=name).first():
        return make_response(False, 'Club with this name or code already exists.', 409)
    data['tags'] = tags
    data['code'] = code
    data['owner'] = current_user.username
    club = create_club(data)
    club.members.append(current_user)
    cache.delete_memoized(get_clubs)
    db.session.commit()
    return jsonify(club.to_dict()), 201

@club.route('/<code>/', methods=['GET'])
@cache.memoize(timeout=600)
def get_club(code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'No club with this code found', 404)
    return jsonify(club.to_dict()), 200

@club.route('/<code>/', methods=['PUT'])
@token_required
def modify_club(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'No club with this code found.', 404)
    data = request.get_json()
    if 'code' not in data or data['code'] != club.code:
        return make_response(False, 'Given codes do not match.', 400)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners may modify clubs.', 403)
    if 'name' in data:
        name = data['name']
        if Club.query.filter_by(name=name).first():
            return make_response(False, 'Club with this name already exists.', 409)
        club.name = name
    if 'description' in data:
        club.description = data['description']
    if 'tags' in data:
        tags = [tag['name'] for tag in data['tags']]
        club.tags = [get_or_create(tag) for tag in tags]
    db.session.commit()
    cache.delete_memoized(get_club)
    cache.delete_memoized(get_clubs)
    return jsonify(club.to_dict()), 201

@club.route('/<code>/', methods=['DELETE'])
@token_required
def delete_club(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'No club with this code found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners can delete a club.', 403)
    db.session.delete(club)
    db.session.commit()
    cache.delete_memoized(get_clubs)
    cache.delete_memoized(get_club)
    return make_response(True, 'Club successfully deleted.', 200)

@club.route('/<code>/members/', methods=['GET'])
@cache.memoize(timeout=600)
def get_club_members(code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    members = club.members
    return jsonify_users(members), 200

@club.route('/<code>/members/', methods=['POST'])
@token_required
def add_club_member(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners can add members to a club.', 403)
    data = request.get_json()
    if 'username' not in data:
        return make_response(False, 'Required username field not found.', 400)
    username = data['username']
    new_member = User.query.filter_by(username=username).first()
    if not new_member:
        return make_response(False, 'User with that username not found.', 404)
    if new_member in club.members:
        return make_response(False, 'User to be added is already a member.', 409)
    club.members.append(new_member)
    db.session.commit()
    cache.delete_memoized(get_club_members)
    return jsonify(new_member.to_dict()), 201

@club.route('/<code>/members/<username>', methods=['DELETE'])
@token_required
def delete_club_member(current_user, code, username):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners may remove members.', 403)
    former_member = User.query.filter_by(username=username).first()
    if former_member not in club.members:
        return make_response(False, 'No member with that username found.', 404)
    if former_member == current_user:
        return make_response(False, 'Club owners may not remove themselves as members.', 409)
    club.members.remove(former_member)
    db.session.commit()
    cache.delete_memoized(get_club_members)
    return make_response(True, 'Member successfully removed.', 200)

@club.route('/<code>/files', methods=['GET'])
@cache.memoize(timeout=600)
def get_club_files(code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'No such club found.', 404)
    from app import app
    club_folder = os.path.join(app.config.get('UPLOAD_FOLDER'), code)
    if not os.path.isdir(club_folder):
        return make_response(False, 'No files found for this club.', 404)
    files = os.listdir(club_folder)
    return jsonify_files(files), 200

@club.route('/<code>/files', methods=['POST'])
@token_required
def add_club_file(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners may upload files.', 403)
    file = request.files['file']
    if not file:
        return make_response(False, 'File not found in request form data.', 400)
    if not (file.filename and file_is_allowed(file.filename)):
        return make_response(False, 'File type not supported.', 400)
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    from app import app
    club_folder = os.path.join(app.config.get('UPLOAD_FOLDER'), code)
    if not os.path.isdir(club_folder):
        os.makedirs(club_folder)
    filepath = os.path.join(club_folder, filename)
    if os.path.exists(filepath):
        return make_response(False, 'Filename already taken.', 409)
    file.save(filepath)
    cache.delete_memoized(get_club_files)
    return make_response(True, '{} uploaded to {}'.format(filename, filepath), 201)

@club.route('/<code>/files/<filename>', methods=['GET'])
@cache.memoize(timeout=60)
def get_club_file(code, filename):
    from app import app
    club_folder = os.path.join(app.config.get('UPLOAD_FOLDER'), code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        return make_response(False, 'No file with this filename exists.', 404)
    from flask import send_from_directory
    return send_from_directory(club_folder, filename, as_attachment=True), 200

@club.route('/<code>/files/<filename>', methods=['PUT'])
@token_required
def modify_club_file(current_user, code, filename): 
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners can modify club files.', 403)
    from app import app
    club_folder = os.path.join(app.config.get('UPLOAD_FOLDER'), code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        return make_response(False, 'No such file found.', 404)
    file = request.files['file']
    if not file:
        return make_response(False, 'File not found in request.', 400)
    if not (file.filename and file_is_allowed(file.filename)):
        return make_response(False, 'File type not supported.', 400)
    file.save(filepath)
    cache.delete_memoized(get_club_file)
    cache.delete_memoized(get_club_files)
    return make_response(True, '{} successfully replaced at {}'.format(filename, club_folder), 201)

@club.route('/<code>/files/<filename>', methods=['DELETE'])
@token_required
def delete_club_file(current_user, code, filename):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    club_owner = User.query.filter_by(username=club.owner).first()
    if club_owner and current_user != club_owner:
        return make_response(False, 'Only club owners can delete club files.', 403)
    from app import app
    club_folder = os.path.join(app.config.get('UPLOAD_FOLDER'), code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        return make_response(False, 'File with this filepath not found.', 404)
    os.remove(filepath)
    cache.delete_memoized(get_club_file)
    cache.delete_memoized(get_club_files)
    return make_response(True, '{} successfully deleted.'.format(filepath), 200)

@club.route('/<code>/comments/', methods=['GET'])
@cache.memoize(timeout=60)
def get_club_comments(code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    comments = Comment.query.filter_by(club_id=club.id).all()
    if request.args.get('search'):
        comments = comments.query.filter(user_id=request.args.get('search'))
    return jsonify_comments(comments), 200

@club.route('/<code>/comments/<comment_id>', methods=['GET'])
@cache.memoize(timeout=60)
def get_comment(code, comment_id):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    comment = Comment.query.get(comment_id)
    if not comment:
        return make_response(False, 'Comment with this ID not found.', 404)
    subcomments = Comment.query.filter_by(parent_id=comment.id).all()
    if len(subcomments) != 0:
        return jsonify_comments(subcomments), 200
    return jsonify(comment.to_dict()), 200

@club.route('/<code>/comments/', methods=['POST'])
@token_required
def add_comment(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    data = request.get_json()
    if 'content' not in data:
        return make_response(False, 'Comment content not found in request.', 400)
    comment = data['content']
    new_comment = Comment(content=comment, user_id=current_user.id, club_id=club.id)
    db.session.add(new_comment)
    db.session.commit()
    cache.delete_memoized(get_club_comments)
    cache.delete_memoized(get_club_comment)
    return jsonify(new_comment.to_dict()), 201

@club.route('/<code>/comments/<comment_id>', methods=['POST'])
@token_required
def add_subcomment(current_user, code, comment_id):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    comment = Comment.query.get(comment_id)
    if not comment:
        return make_response(False, 'Comment with this ID not found.', 404)
    data = request.get_json()
    if 'content' not in data:
        return make_response(False, 'Comment content not found in request.', 400)
    comment = data['content']
    new_comment = Comment(content=comment, user_id=current_user.id, club_id=club.id, parent_id=comment_id)
    db.session.add(new_comment)
    db.session.commit()
    cache.delete_memoized(get_club_comments)
    cache.delete_memoized(get_club_comment)
    return jsonify(new_comment.to_dict()), 201

@club.route('/<code>/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_club_comment(current_user, code, comment_id):
    club = Club.query.filter_by(code=code).first()
    if not club:
        return make_response(False, 'Club with this code not found.', 404)
    comment = Comment.query.get(comment_id)
    if not comment:
        return make_response(False, 'Comment with this ID not found.', 404)
    comment_owner = User.query.get(comment.user_id)
    if comment_owner != current_user:
        return make_response(False, 'You can only delete your own comments.', 403)
    db.session.delete(comment)
    db.session.commit()
    cache.delete_memoized(get_club_comments)
    cache.delete_memoized(get_club_comment)
    return make_response(True, 'Comment successfully deleted.', 200)
