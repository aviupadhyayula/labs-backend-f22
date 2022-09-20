from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

DB_FILE = "clubreview.db"

app = Flask(__name__)
cache = Cache(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
app.config['SECRET_KEY'] = 'pennlabs'
app.config['UPLOAD_FOLDER'] = 'club_files'
db = SQLAlchemy(app)

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorator(*args, **kwargs):
        from utils import make_response, validate_token, decode_token
        token = None
        if 'auth_token' in request.headers:
            token = request.headers.get('auth_token')
        if not token:
            return make_response(False, 'A valid auth token is missing', 401)
        if not validate_token(token):
            return make_response(False, 'Your auth token is invalid/has expired.', 401)
        from models import User
        username = decode_token(token)
        current_user = User.query.filter_by(username=username).first()
        return f(current_user, *args, **kwargs)
    return decorator

from views.club import club
from views.tag import tag
from views.auth import auth
from views.user import user
from views.favorite import favorite
app.register_blueprint(club)
app.register_blueprint(tag)
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(favorite)

@app.route('/')
def main():
    return "Welcome to Penn Club Review!"

@app.route('/api')
def api():
    return jsonify({"message": "Welcome to the Penn Club Review API!."}), 200

if __name__ == '__main__':
    app.run()
