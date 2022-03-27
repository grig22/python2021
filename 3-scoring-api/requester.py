import requests
import json
import hashlib
import datetime

BASE_URL = 'http://localhost'
PORT = 8080

endpoint = 'method'
url = f'{BASE_URL}:{PORT}/{endpoint}/'
headers = {'Content-Type': 'application/json'}

if 7777:
    account = 'Google Inc.'
    login = 'username'
    SALT = "Otus"
    key = account + login + SALT
else:
    account = 'Google Inc.'
    login = 'admin'
    SALT = "42"
    key = datetime.datetime.now().strftime("%Y%m%d%H") + SALT
key = key.encode()
token = hashlib.sha512(key).hexdigest()

data = {
    'account': account,
    'login': login,
    # 'method': 'clients_interests',
    'method': 'online_score',
    'token': token,
    # 'arguments': {'client_ids': [1, 2, 3, 4], "date": "20.07.2017"},
    'arguments': {"phone": "79175002040", "email": "stupnikov@otus.ru",
                  "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1},
}

res = requests.post(url=url, headers=headers, data=json.dumps(data))
print(f'CODE = "{res.status_code}"')
print(f'TEXT = "{res.text}"')