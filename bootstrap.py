import os
from app import db, DB_FILE

def create_user():
    from models import User
    import bcrypt
    josh = User(username='josh', email='josh@seas.upenn.edu', password=bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()))
    db.session.add(josh)
    db.session.commit()

def load_data():
    from utils import create_club
    import json
    with open('clubs.json', 'r') as f:
        data = json.load(f)
        for entry in data:
            create_club(entry)
    import scraper
    scraper.scrape_ocwp()

# No need to modify the below code.
if __name__ == '__main__':
    # Delete any existing database before bootstrapping a new one.
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db.create_all()
    create_user()
    load_data()
