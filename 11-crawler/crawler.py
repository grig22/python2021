#!/usr/bin/python3.9

import requests

re = requests.get(url='https://news.ycombinator.com/')
print(re.text)
