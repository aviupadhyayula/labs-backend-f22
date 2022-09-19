from bs4 import BeautifulSoup
import requests
import re

def main():
    from utils import create_club, create_club_code
    from models import Club, User
    josh = User.query.filter_by(username='josh').first()
    page = requests.get('https://ocwp.pennlabs.org/')
    soup = BeautifulSoup(page.text, 'html.parser')
    clubs = soup.find_all('div', style=re.compile('important'))
    for club in clubs:
        name = club.find('strong', class_='club-name').text
        code = create_club_code(name)
        description = club.find('em').text
        tags = [tag.text for tag in club.find_all('span', class_=re.compile('tag'))]
        create_club({"code": code, "name": name, "description": description, "tags": tags, 'owner': 'josh'})

if __name__ == '__main__':
    main()
