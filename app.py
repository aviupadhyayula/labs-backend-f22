from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

DB_FILE = "clubreview.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
app.config['SECRET_KEY'] = 'pennlabs'
app.config['UPLOAD_FOLDER'] = 'club_files'
app.config['FLASK_DEBUG'] = 1
db = SQLAlchemy(app)

import os
from models import *
from utils import *
import bcrypt
from flask import redirect, url_for, abort

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'auth_token' in request.headers:
            token = request.headers.get('auth_token')
        if not token:
            return jsonify({'message': 'A valid auth token is missing.'}), 401
        if not validate_token(token):
            return jsonify({'message': 'Your auth token is invalid/has expired. Log in again.'}), 401
        username = decode_token(token)
        current_user = User.query.filter_by(username=username).first()
        return f(current_user, *args, **kwargs)
    return decorator

@app.route('/')
def main():
    return "Welcome to Penn Club Review!"

@app.route('/api')
def api():
    return jsonify({"message": "Welcome to the Penn Club Review API!."}), 200

@app.route('/api/clubs/', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    if request.args.get('search'):
        search = '%{}%'.format(request.args.get('search'))
        clubs = Club.query.filter(Club.name.like(search)).all()
    return jsonify_clubs(clubs), 200

@app.route('/api/clubs/', methods=['POST'])
@token_required
def add_club(current_user):
    data = request.get_json()
    print(data)
    if 'name' not in data or 'tags' not in data:
        abort(400, 'name or tags missing')
    name = data['name']
    tags = [tag['name'] for tag in data['tags']]
    code = create_club_code(name)
    if 'code' in data:
        code = create_club_code(data['code'])
    if Club.query.filter_by(code=code).first() or Club.query.filter_by(name=name).first():
        abort(409, 'club with this name or code already exists')
    data['tags'] = tags
    data['code'] = code
    data['owner'] = current_user.username
    club = create_club(data)
    return jsonify(club.to_dict()), 201

@app.route('/api/clubs/<code>/', methods=['GET'])
def get_club(code):
    club = Club.query.filter_by(code=code).first()
    if club is None:
        abort(404, 'no matching clubs found')
    return jsonify(club.to_dict()), 200

@app.route('/api/clubs/<code>/', methods=['PUT'])
@token_required
def modify_club(code, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no matching clubs found')
    data = request.get_json()
    if 'code' not in data or data['code'] != club.code:
        abort(400, 'codes do not match')
    if current_user != club.owner:
        abort(403, 'only club owners can modify a club')
    if 'name' in data:
        name = data['name']
        if Club.query.filter_by(name=name).first():
            abort(409, 'club with this name already exists')
        club.name = name
    if 'description' in data:
        club.description = data['description']
    if 'tags' in data:
        tags = [tag['name'] for tag in data['tags']]
        club.tags = [get_or_create(tag) for tag in tags]
    db.session.commit()
    return jsonify(club.to_dict()), 201

@app.route('/api/clubs/<code>/', methods=['DELETE'])
@token_required
def delete_club(code, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no matching clubs found')
    if current_user != club.owner:
        abort(403, 'only club owners can delete a club')
    db.session.delete(club)
    db.session.commit()
    return jsonify(), 204

@app.route('/api/clubs/<code>/members/', methods=['GET'])
def get_club_members(code, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'club with this code not found')
    members = club.members
    return jsonify_users(members), 200

@app.route('/api/clubs/<code>/members/', methods=['POST'])
@token_required
def add_club_members(code, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no such club found')
    if current_user != club.owner:
        abort(403, 'only club owners can add members to a club')
    data = request.get_json()
    if 'username' not in data:
        abort(409, 'member to be added not found')
    username = data['username']
    new_member = User.query.filter_by(username=username).first()
    if not new_member:
        abort(404, 'no user with matching username found')
    if new_member in club.members:
        abort(409, 'member to be added already in club')
    club.members.append(new_member)
    db.session.commit()
    return jsonify(new_member.to_dict()), 201

@app.route('/api/clubs/<code>/members/<username>', methods=['DELETE'])
@token_required
def delete_club_member(code, username, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no such club found')
    if user != club.owner:
        abort(403, 'only club owners can remove members from a club')
    former_member = User.query.filter_by(username=username).first()
    if former_member not in club.members:
        abort(404, 'no member with matching username found')
    club.members.remove(former_member)
    db.session.commit()
    return jsonify(), 204

@app.route('/api/clubs/<code>/files', methods=['GET'])
def get_club_files(code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no such club found')
    club_folder = os.path.join(app.config['UPLOAD_FOLDER'], code)
    if not os.path.isdir(club_folder):
        return jsonify(), 200
    files = os.listdir(club_folder)
    return jsonify_files(files), 200

@app.route('/api/clubs/<code>/files', methods=['POST'])
@token_required
def add_club_file(current_user, code):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no such club found')
    file = request.files['file']
    if not file:
        abort(400, 'file not found')
    if not (file.filename and file_is_allowed(file.filename)):
        abort(400, 'file type not supported')
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    club_folder = os.path.join(app.config['UPLOAD_FOLDER'], code)
    if not os.path.isdir(club_folder):
        os.makedirs(club_folder)
    filepath = os.path.join(club_folder, filename)
    if os.path.exists(filepath):
        abort(409, 'file with same filename already exists')
    file.save(filepath)
    responseObject = {
        'status': 'successful',
        'message': '{} uploaded to {}'.format(filename, filepath)
    }
    return jsonify(responseObject), 201

@app.route('/api/clubs/<code>/files/<filename>', methods=['GET'])
def get_club_file(club_code, filename):
    club_folder = os.path.join(app.config['UPLOAD_FOLDER'], club_code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        abort(404, 'no such file exists')
    from flask import send_from_directory
    return send_from_directory(club_folder, filename, as_attachment=True), 200

@app.route('/api/clubs/<code>/files/<filename>', methods=['PUT', 'PATCH'])
@token_required
def modify_club_file(club_code, filename, current_user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no matching club found')
    if user != club.owner:
        abort(403, 'only club owners can modify club files')
    club_folder = os.path.join(app.config['UPLOAD_FOLDER'], club_code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        abort(404, 'no such file found')
    file = request.files['file']
    if not file:
        abort(400, 'replacement file not found')
    if not (file.filename and is_allowed(file.filename)):
        abort(400, 'file type not supported')
    file.save(filepath)
    return jsonify(), 201

@app.route('/api/clubs/<code>/files/<filename>', methods=['DELETE'])
@token_required
def delete_club_file(club_code, filename, current_user):
    club = Club.query.filter_by(code=club_code).first()
    if not club:
        abort(404, 'no matching club found')
    if user != club.owner:
        abort(403, 'only club owners can modify club files')
    club_folder = os.path.join(app.config['UPLOAD_FOLDER'], club_code)
    filepath = os.path.join(club_folder, filename)
    if not os.path.exists(filepath):
        abort(404, 'no such file found')
    os.remove(filepath)
    return jsonify(), 204

@app.route('/api/clubs/<code>/comments/', methods=['GET'])
def get_club_comments(club_code):
    club = Club.query.filter_by(code=club_code).first()
    if not club:
        abort(404, 'no matching club found')
    comments = Comment.query.filter_by(club_id=club.id).all()
    if request.args.get('search'):
        comments = comments.query.filter(user_id=request.args.get('search'))
    return jsonify_comments(comments), 200

@app.route('/api/clubs/<code>/comments/<comment_id>', methods=['POST'])
@token_required
def add_subcomment(club_code, comment_id, current_user):
    club = Club.query.filter_by(code=club_code).first()
    if not club:
        abort(404, 'no matching club found')
    comment = Comment.query.get(comment_id)
    if not comment or comment.club_id != club.id:
        abort(404, 'no matching comment found')
    data = request.get_json()
    if not 'content' in data:
        abort(400, 'no comment data found')
    new_comment = comment(content=data['content'], user_id=current_user.id, club_id=club.id, parent_id=comment_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify(new_comment.to_dict()), 201

@app.route('/api/clubs/<code>/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_club_comment(club_code, comment_id, current_user):
    club = Club.query.filter_by(code=club_code).first()
    if not club:
        abort(404, 'no matching club found')
    comment = Comment.query.get(comment_id)
    if not comment or comment.club_id != club.id:
        abort(404, 'no matching comment found')
    if current_user.id != comment.user_id:
        abort(401, 'only authors of a comment may delete it')
    db.session.delete(comment)
    db.session.commit()


@app.route('/api/favorites/', methods=['GET'])
@token_required
def get_favorites(user):
    clubs = [club for club in user.favorite_clubs]
    return jsonify_clubs(clubs), 200
    
@app.route('/api/favorites/', methods=['POST'])
@token_required
def add_favorite(user):
    data = request.get_json()
    if 'code' not in data:
        abort(400, 'club code missing')
    code = data['code']
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no matching club found')
    user.favorites.append(club)
    return jsonify(code), 201

@app.route('/api/favorites/<club_code>', methods=['DELETE'])
@token_required
def remove_favorite(code, user):
    club = Club.query.filter_by(code=code).first()
    if not club:
        abort(404, 'no such club exists')
    if user not in club.members:
        abort(404, 'user not found in club membrs')
    user.favorites.remove(club)
    db.session.commit()
    return jsonify(), 204

@app.route('/api/tags/', methods=['GET'])
def get_tags():
    tags = Tag.query.all()
    return jsonify_tags(tags), 200

@app.route('/api/users/<username>', methods=['GET'])
@token_required
def get_user(username, user):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(400, 'no matching users found')
    return jsonify(user.to_dict()), 200

@app.route('/api/users/<username>', methods=['PUT'])
@token_required
def modify_user(username, current_user):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404, 'no such user exists')
    if user != current_user:
        abort(403, 'you can only edit your own user information')
    data = request.get_json()
    if 'username' not in dta or data['username'] != username:
        abort(400, 'usernames do not match')
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        new_password = data['password'].encode('utf8')
        user.password = bcrypt.hashpw(new_password, bcrypt.gensalt())
    db.session.commit()
    return jsonify(current_user.to_dict()), 201

@app.route('/api/users/<username>', methods=['DELETE'])
@token_required
def delete_user(username, current_user):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404, 'no matching user found')
    if user != current_user:
        abort(403, 'you can only delete your own user profile')
    invalidate_token(request.headers.get('auth_token'))
    db.session.delete(current_user)
    db.session.commit()
    return jsonify(), 204

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required = ['username', 'email', 'password']
    if not all(item in data for item in required):
        abort(400, 'missing credentials')
    username = data['username'].lower()
    email = data['email'].lower()
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        abort(409, 'user with username and/or email already exists')
    password = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect('/api/login', code=201)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    required = ['username', 'password']
    if not all(item in data for item in required):
        abort(400, 'missing credentials')
    username = data['username']
    password = data['password'].encode('utf-8')
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password, user.password):
        abort(401, 'invalid authentication credentials')
    token = create_token(username)
    responseObject = {
        'status': 'success',
        'message': 'Successfully logged in.',
        'auth_token': token
    }
    return jsonify(responseObject), 200

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(user):
    token = request.headers.get('auth_token')
    invalidate_token(token)
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run()
