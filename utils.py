from app import db

def create_club(club):
    from models import Club
    tags = club.pop('tags')
    tags = [get_or_create_tag(tag_name) for tag_name in tags]
    club = Club(**club)
    club.tags.extend(tags)
    db.session.add(club)
    db.session.commit()
    return club

def get_or_create_tag(tag_name):
    from models import Tag
    tag = Tag.query.filter_by(name=tag_name).first()
    if tag is None:
        tag = Tag(name=tag_name)
        db.session.add(tag)
        db.session.commit()
    return tag

def jsonify_comments(comments):
    comments_dict = [comment.to_dict() for comment in comments]
    return comments_dict

def jsonify_users(users):
    users_dict = [user.to_dict() for user in users]
    return users_dict

def jsonify_clubs(clubs):
    clubs_dict = [club.to_dict() for club in clubs]
    return clubs_dict

def jsonify_tags(tags):
    tags_dict = [tag.to_dict() for tag in tags]
    return tags_dict

def jsonify_files(files):
    files_dict = [{"filename": file} for file in files]
    return files_dict

def create_club_code(club_name):
    import re
    code = re.sub('/^([!#$&-;=?-[]_a-z~]|%[0-9a-fA-F]{2})+$/', '-', club_name.lower())
    code = code.replace(' ', '-')
    return code

def create_token(username):
    from flask import current_app
    import datetime
    import jwt
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': username
    }
    return jwt.encode(payload, current_app.config.get('SECRET_KEY'), algorithm='HS256')

def validate_token(token):
    from models import InvalidToken
    if InvalidToken.query.filter_by(id=token).first():
        return False
    from flask import current_app
    import jwt
    try:
        payload = jwt.decode(token, current_app.config.get('SECRET_KEY'), algorithms='HS256')
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def decode_token(token):
    from flask import current_app
    import jwt
    payload = jwt.decode(token, current_app.config.get('SECRET_KEY'), algorithms='HS256')
    return payload['sub']

def invalidate_token(token):
    from models import InvalidToken
    blacklist = InvalidToken(id=token)
    db.session.add(blacklist)
    db.session.commit()

def file_is_allowed(filename):
    ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']
    file_extension = ""
    i = len(filename) - 1
    while filename[i] != '.':
        file_extension = filename[i] + file_extension
        i -= 1
    return file_extension.lower() in ALLOWED_EXTENSIONS
