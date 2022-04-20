#!/usr/bin/python3.9
import requests
from bs4 import BeautifulSoup

URL = 'https://news.ycombinator.com/'
re = requests.get(url=URL)
html_doc = re.text
# print(html_doc.text)
soup = BeautifulSoup(html_doc, 'html.parser')
# print(soup.prettify())

for link in soup.find_all(attrs={'class': "titlelink"}):
    href = link.get('href')
    if href.startswith('item?id='):
        href = URL + href
    print(href)
