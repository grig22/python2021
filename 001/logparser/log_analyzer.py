#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import re
import statistics
import json
import sys
import os
import datetime
import collections


def split_filenames(names):
    regexp = r'nginx-access-ui\.log-(\d+).?(\S*)'
    prog = re.compile(regexp)
    Filename = collections.namedtuple('Filename', 'name date extension')
    for name in names:
        try:
            result = prog.match(name)
            dd = result.group(1)
            date = datetime.date.fromisoformat(f'{dd[0:4]}-{dd[4:6]}-{dd[6:8]}')
        except:
            continue
        else:
            yield Filename(name=name, date=date, extension=result.group(2))


def get_last_log(log_dir):
    return sorted(split_filenames(os.listdir(log_dir)), key=lambda x: x.date, reverse=True)[0]


def yield_lines(filename, extension):
    opener = {'gz': gzip.open}.get(extension, open)
    with opener(filename, mode='rt', encoding="utf-8") as fd:
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
def stat(collector, report_size):
    overall = {
        'time': 0.0,
        'count': 0.0,
    }
    for url in collector:
        times = list(map(float, collector[url]))
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
        collector[url] = stats
    # второй проход - когда посчитаны overall
    for url in collector:
        stats = collector[url]
        stats['time_perc'] = 100 * stats['time_sum'] / overall['time']
        stats['count_perc'] = 100 * stats['count'] / overall['count']
        # kinda post-processing
        for k, v in stats.items():
            if isinstance(v, float):
                stats[k] = round(v, 3)
    return sorted(list(collector.values()), key=lambda x: x['time_sum'], reverse=True)[:report_size]


def save_report(data, report_dir, report_fullname):
    os.makedirs(report_dir, exist_ok=True)
    with open('report.html', mode='rt', encoding="utf-8") as fi:
        body = fi.read().replace('$table_json', json.dumps(data, ensure_ascii=False))
    with open(report_fullname, mode='wt', encoding="utf-8") as fo:
        fo.write(body)


def apply_config(config, filename):
    print(f'Используем файл конфигурации "{filename}"')
    if os.stat(filename).st_size == 0:
        return
    with open(filename, mode='rt', encoding="utf-8") as ff:
        conf_json = json.load(ff)
        for k in conf_json:
            if k in config:
                config[k] = conf_json[k]


def main():
    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",  # TODO
        "LOG_DIR": "./log",  # TODO
    }
    collector = dict()
    try:
        if len(sys.argv) >= 2 and sys.argv[1] == '--config':
            apply_config(config, sys.argv[2])
        print(f'Параметры конфигурации {config}')
        log_dir = config['LOG_DIR']
        report_dir = config['REPORT_DIR']
        name, date, ext = get_last_log(log_dir)
        report_fullname = f'{report_dir}/report-{date.isoformat().replace("-", ".")}.html'
        if os.path.isfile(report_fullname):
            raise Exception(f'Файл "{report_fullname}" уже существует, всё отменяется')
        log_fullname = f'{log_dir}/{name}'
        for data in parse(yield_lines(log_fullname, ext)):
            push(collector, data)
        report = stat(collector=collector, report_size=config['REPORT_SIZE'])
        save_report(data=report, report_dir=report_dir, report_fullname=report_fullname)
    except Exception as ex:
        print(f'ВОЗНИКЛО ИСКЛЮЧЕНИЕ в строке {sys.exc_info()[2].tb_lineno}: {sys.exc_info()[0].__name__} "{ex}"')
        raise


if __name__ == "__main__":
    main()
