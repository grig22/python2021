#!/usr/bin/python3.9
# import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import os
import pathlib

import asyncio
import aiofiles
# import aiohttp
from aiohttp import ClientSession

# https://realpython.com/async-io-python/#a-full-program-asynchronous-requests

MAINPAGE = 'https://news.ycombinator.com/'
DUMPDIR = 'pages/'


async def fetch_html(session: ClientSession, url: str) -> str:
    resp = await session.request(method="GET", url=url)
    resp.raise_for_status()
    html = await resp.text()
    return html


async def parse_mainpage(session: ClientSession):
    text = await fetch_html(url=MAINPAGE, session=session)
    soup = BeautifulSoup(text, 'html.parser')
    title_soup = soup.find_all(attrs={'class': "titlelink"})  # <a class="titlelink" href="item?id=31093910">
    hrefs = map(lambda title: title.get('href'), title_soup)
    links = map(lambda href: MAINPAGE + href if href.startswith('item?id=') else href, hrefs)
    hide_soup = soup.find_all(href=re.compile('^hide\?id='))  # <a href="hide?id=31093910&amp;goto=news">
    comments = map(lambda hide: MAINPAGE + 'item?id=' + str(hide).partition('id=')[2].rpartition('&amp;')[0], hide_soup)
    return list(zip(links, comments))  # yield?


async def download_page(session: ClientSession, dirname: str, url: str):
    try:
        text = await fetch_html(url=url, session=session)
        text = text.encode('utf-8')
        filename = f"{dirname}/{urllib.parse.quote(string=url, safe='')}"
        async with aiofiles.open(filename, "wb") as fd:
            fd.write(text)
    except Exception as ex:
        print(f'! EXCEPTION {ex}')


async def download_all(session: ClientSession, dirname: str, title_url: str, comments_urls: set):
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
    await download_page(session=session, dirname=dirname, url=title_url)
    await asyncio.gather(*[download_page(session=session, dirname=dirname, url=url) for url in comments_urls])


async def fetch_comments_urls(session: ClientSession, comments_page: str):
    print('COMMENTS', comments_page)
    text = await fetch_html(session, url=comments_page)
    soup = BeautifulSoup(text, 'html.parser')  # print(soup.prettify())
    accum = set()
    comments = soup.find_all(attrs={'class': "commtext"})
    for comm in comments:
        accum = accum | set(tag.get('href') for tag in comm.find_all(name='a'))
    return accum


async def crawl(session: ClientSession, title_page: str, comments_page: str):
    dirname = DUMPDIR + urllib.parse.quote(title_page, safe='')
    if os.path.exists(dirname):
        print(f'SKIP {title_page}')
    else:
        print(f'DOWNLOAD {title_page}')
        comments_urls = await fetch_comments_urls(session=session, comments_page=comments_page)
        await download_all(session=session, dirname=dirname, title_url=title_page, comments_urls=comments_urls)


async def main():
    async with ClientSession() as session:
        big_list = await parse_mainpage(session)
        await asyncio.gather(*[crawl(session=session, title_page=title_page, comments_page=comments_page)
                               for title_page, comments_page in big_list])


if __name__ == '__main__':
    asyncio.run(main())
