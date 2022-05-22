#!/usr/bin/python3.10

from bs4 import BeautifulSoup
import re
import urllib.parse
import os
import pathlib
import asyncio
import aiofiles
from aiohttp import ClientSession
import random
import json

# https://realpython.com/async-io-python/#a-full-program-asynchronous-requests

MAINPAGE = 'https://news.ycombinator.com/'
DUMPDIR = 'pages/'
GLOBAL_TOTAL_FAIL = list()
NUM_RETRY_MAIN = 30
NUM_RETRY_OTHER = 4
PREPARE_TO_FETCH = 2
MAGIC_RANGE = (4.0, 8.0)


async def fetch_html(session: ClientSession, url: str) -> str:
    # если наседать, кидает 503  # 2. L26
    # 503, message='Service Temporarily Unavailable', url=URL('https://news.ycombinator.com/item?id=31104691')
    await asyncio.sleep(PREPARE_TO_FETCH)
    # а если быть настойчивым, то банят на некоторое время
    # 403, message='Forbidden', url=URL('https://news.ycombinator.com/item?id=14661659')
    how_long = NUM_RETRY_MAIN if url.startswith(f'{MAINPAGE}item?id=') else NUM_RETRY_OTHER  # 1. L30
    for retry in range(how_long):
        try:
            resp = await session.request(method="GET", url=url)
            resp.raise_for_status()
            html = await resp.text()
            if retry > 0:
                print(f'fetched on retry {retry}: {url}')
            return html
        except Exception as ex:
            print(f'! HTTP EXCEPTION on retry {retry}: {ex}')
            magic_seconds = random.uniform(*MAGIC_RANGE)  # 3. L41
            await asyncio.sleep(magic_seconds)
            continue
    print(f'!! TOTALLY FAILED: {url}')
    GLOBAL_TOTAL_FAIL.append(url)
    return ''


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
    text = await fetch_html(url=url, session=session)
    text = text.encode('utf-8')
    filename = f"{dirname}/{urllib.parse.quote(string=url, safe='')}"
    try:
        # есть вероятность, что будет повтор имени файла, и что контент будет разный
        # можно дописывать к каждому UUID или инкремент
        # но для простоты предлагаю пока просто перезаписывать содержимое
        async with aiofiles.open(filename, "wb") as fd:  # 4. L65
            await fd.write(text)
    except Exception as ex:
        print(f'! FILE EXCEPTION {ex}')


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
        print('GLOBAL_TOTAL_FAIL')
        print(json.dumps(sorted(GLOBAL_TOTAL_FAIL), indent=2))


if __name__ == '__main__':
    asyncio.run(main())


# + 1. L30 - кусок url лучше подставлять из констант\конфигов чтобы не плодить копипасту
# + 2. L26 - круто, что нашли, можно сделать параметр ожидания между запросами и вынести его в конфиг
# + 3. L41 - тоже лучше вынести в параметр
# ? 4. L65 - а есть вероятность, что получится 2 одинаковых имени файла?
