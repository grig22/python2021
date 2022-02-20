import requests
import json

BASE_URL = 'http://localhost'
PORT = 8080

endpoint = 'method'
url = f'{BASE_URL}:{PORT}/{endpoint}/'
headers = {'Content-Type': 'application/json'}

data = {
    'account': 'Google Inc.',
    'login': 'username',
    # 'method': 'clients_interests',
    'method': 'online_score',
    'token': '123456',
    # 'arguments': {'client_ids': [1, 2, 3, 4], "date": "20.07.2017"},
    'arguments': {"phone": "79175002040", "email": "stupnikov@otus.ru",
                  "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1},
}

res = requests.post(url=url, headers=headers, data=json.dumps(data))
print(f'CODE = "{res.status_code}"')
print(f'TEXT = "{res.text}"')
