from app import db

# Your database models should go here.
# Check out the Flask-SQLAlchemy quickstart for some good docs!
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/

user_to_club = db.Table('user_to_club',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'))
)

tag_to_club = db.Table('tag_to_club',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'))
)

owner_to_club = db.Table('owner_to_club',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'))
)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.Text, nullable=True)
    owner = db.Column(db.String(150), db.ForeignKey('user.username'))
    tags = db.relationship('Tag', secondary=tag_to_club, back_populates='clubs')
    members = db.relationship('User', secondary=user_to_club, back_populates='clubs')
    favorites = db.relationship('User', secondary=favorites, back_populates='favorites')
    def to_dict(self):
        return {'id': self.id, 'code': self.code, 'name': self.name, 'description': 
                self.description, 'membership_count': len(self.members), 'tags': 
                [tag.to_dict() for tag in self.tags], 'favorite_count': len(self.favorites)}

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    clubs = db.relationship('Club', secondary=tag_to_club, back_populates='tags')
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'clubs': len(self.clubs)}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(254))
    clubs = db.relationship('Club', secondary=user_to_club, back_populates='members')
    owned_clubs = db.relationship('Club', backref='owner.username')
    favorites = db.relationship('Club', secondary=favorites, back_populates='favorites')
    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email}

class InvalidToken(db.Model):
    id = db.Column(db.String(255), primary_key=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    club_id = db.Column(db.Integer, nullable=False)
    parent_id = db.Column(db.Integer, nullable=True)
    def to_dict(self):
        return {'id': self.id, 'user': self.user_id, 'club': self.club_id, 'content': self.content, 'parent': self.parent_id}
