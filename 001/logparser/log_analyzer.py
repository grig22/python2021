#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import re
import statistics

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def filename():
    # TODO честно выбирать из многих файлов
    # TODO проверять время в имени файла и что есть ли для него уже отчёт
    return 'nginx-access-ui.log-20170630.gz'


def lines(name):
    ext = name.split('.')[-1]
    opener = {
        'gz': gzip.open,
    }.get(ext, open)
    with opener(name, mode='rt', encoding="utf-8") as fd:
        for line in fd:
            yield line


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
def parse(text):
    regexp = r'\S+\s+\S+\s+\S+\s+\[.+?\]\s+\"\S+\s+(.+?)\s+\S+\".*\s+(\S+)'
    prog = re.compile(regexp)
    for line in text:
        result = prog.match(line)  # TODO считать ошибки
        yield result.group(1, 2)


def push(coll, data):
    url, time = data
    print('push -->', url, time)
    if url not in coll.keys():
        coll[url] = list()
    coll[url].append(time)
    pass


# "url": "/api/v2/internal/html5/phantomjs/queue/?wait=1m",
# {"count": 2767, - сколько раз встречается URL, абсолютное значение
# "time_avg": 62.994999999999997, - средний $request_time для данного URL'а
# "time_max": 9843.5689999999995, - максимальный $request_time для данного URL'а
# "time_sum": 174306.35200000001, - суммарный $request_time для данного URL'а, абсолютное значение
# "time_med": 60.073, - медиана $request_time для данного URL'а

# "time_perc": 9.0429999999999993, - суммарный $request_time для данного URL'а,
#   в процентах относительно общего $request_time всех запросов
# "count_perc": 0.106}  - сколько раз встречается URL, в процентах относительно общего числа запросов
def stat(coll):
    overall = {
        'time': 0.0,
        'count': 0.0,
    }
    for url in coll.keys():
        times = list(map(float, coll[url]))
        stats = {
            'url': url,
            'count': len(times),
            'time_avg': statistics.mean(times),
            'time_max': max(times),
            'time_sum': sum(times),
            'time_med': statistics.median(times),
        }
        overall['time'] += stats['time_sum']
        overall['count'] += stats['count']
        coll[url] = stats
    for url in coll.keys():
        stats = coll[url]
        stats['time_perc'] = 100 * stats['time_sum'] / overall['time']
        stats['count_perc'] = 100 * stats['count'] / overall['count']
        yield stats


def main():
    coll = dict()
    data_iter = parse(lines(filename()))
    count = 0
    for data in data_iter:
        push(coll, data)
        count += 1
        if count > 10:
            break
    for yy in stat(coll):
        print(yy)

if __name__ == "__main__":
    main()
