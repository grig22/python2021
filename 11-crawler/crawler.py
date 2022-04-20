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
    soup = BeautifulSoup(req.text, 'html.parser')
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


def download_all(dirname: str, title_url: str, comments_urls: set):
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
    download_page(dirname, title_url)
    for url in comments_urls:
        download_page(dirname, url)


def fetch_comments_urls(comments_page):
    print('COMMENTS', comments_page)
    req = requests.get(url=comments_page)
    soup = BeautifulSoup(req.text, 'html.parser')
    # print(soup.prettify())
    accum = set()
    comments = soup.find_all(attrs={'class': "commtext"})
    for comm in comments:
        accum = accum | set(tag.get('href') for tag in comm.find_all(name='a'))
    return accum


def main():
    for title_page, comments_page in get_mainpage():
        dirname = DUMPDIR + urllib.parse.quote(title_page, safe='')
        if os.path.exists(dirname):
            print(f'SKIP {title_page}')
            continue
        else:
            print(f'DOWNLOAD {title_page}')
            comments_urls = fetch_comments_urls(comments_page)
            for ii in comments_urls:
                print(ii)
            # download_all(dirname, title_page, comments_urls)


if __name__ == '__main__':
    main()
