#!/usr/bin/python3.9
import requests
from bs4 import BeautifulSoup
import re

URL = 'https://news.ycombinator.com/'
req = requests.get(url=URL)
html_doc = req.text
soup = BeautifulSoup(html_doc, 'html.parser')

# <a class="titlelink" href="item?id=31093910">
titles = soup.find_all(attrs={'class': "titlelink"})
hrefs = map(lambda title: title.get('href'), titles)
links = map(lambda href: URL + href if href.startswith('item?id=') else href, hrefs)
# <a href="hide?id=31093910&amp;goto=news">
hides = soup.find_all(href=re.compile('^hide\?id='))
comments = map(lambda hide: URL + 'item?id=' + str(hide).partition('id=')[2].rpartition('&amp;')[0], hides)
first_line = list(zip(links, comments))
for ff in first_line:
    print(ff)

