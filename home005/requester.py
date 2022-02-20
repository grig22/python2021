import requests
import json

BASE_URL = 'http://localhost'
PORT = 8080

endpoint = 'method'
url = f'{BASE_URL}:{PORT}/{endpoint}/'
headers = {'Content-Type': 'application/json'}

data = {"1111": "2222"}

res = requests.post(url=url, headers=headers, data=json.dumps(data))
print(f'CODE = "{res.status_code}"')
print(f'TEXT = "{res.text}"')
