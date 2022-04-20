#!/usr/bin/python3.9
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import os
import pathlib

MAINPAGE = 'https://news.ycombinator.com/'
DUMPDIR = 'pages/'


def get_mainpage():
    req = requests.get(url=MAINPAGE)
    html_doc = req.text
    soup = BeautifulSoup(html_doc, 'html.parser')
    title_soup = soup.find_all(attrs={'class': "titlelink"})  # <a class="titlelink" href="item?id=31093910">
    hrefs = map(lambda title: title.get('href'), title_soup)
    links = map(lambda href: MAINPAGE + href if href.startswith('item?id=') else href, hrefs)
    hide_soup = soup.find_all(href=re.compile('^hide\?id='))  # <a href="hide?id=31093910&amp;goto=news">
    comments = map(lambda hide: MAINPAGE + 'item?id=' + str(hide).partition('id=')[2].rpartition('&amp;')[0], hide_soup)
    return list(zip(links, comments))  # TODO yield


def download_page(dirname, title_url):
    print(dirname)
    text = requests.get(url=title_url).text.encode('utf-8')
    filename = f"{dirname}/{urllib.parse.quote(title_url, safe='')}"
    print(filename)
    with open(filename, 'wb') as fd:
        fd.write(text)


def download_all(dirname: str, title_url: str, comment_links: list = None):
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
    download_page(dirname, title_url)


def main():
    for ff in get_mainpage():
        title_url, comments_urls = ff
        dirname = DUMPDIR + urllib.parse.quote(title_url, safe='')
        if os.path.exists(dirname):
            print(f'SKIP {title_url}')
            continue
        else:
            print(f'DOWNLOAD {title_url}')
            download_all(dirname, title_url)


if __name__ == '__main__':
    main()
