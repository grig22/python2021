import requests

BASE_URL = 'http://localhost'
PORT = 8080

endpoint = 'method'
url = f'{BASE_URL}:{PORT}/{endpoint}/'

res = requests.post(url=url, data={})
print(f'CODE = "{res.status_code}"')
print(f'TEXT = "{res.text}"')