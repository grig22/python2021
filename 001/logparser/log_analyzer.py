#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import re
import statistics
import json
import sys


def select_filename(conf):
    # TODO честно выбирать из многих файлов
    # TODO проверять время в имени файла и что есть ли для него уже отчёт
    log_dir = conf['LOG_DIR']
    return f'{log_dir}/nginx-access-ui.log-20170630.gz'


def yield_lines(name):
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
def stat(coll, conf):
    overall = {
        'time': 0.0,
        'count': 0.0,
    }
    for url in coll:
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
    # второй проход - когда посчитаны overall
    for url in coll:
        stats = coll[url]
        stats['time_perc'] = 100 * stats['time_sum'] / overall['time']
        stats['count_perc'] = 100 * stats['count'] / overall['count']
        # kinda post-processing
        for k, v in stats.items():
            if isinstance(v, float):
                stats[k] = round(v, 3)
    return sorted(list(coll.values()), key=lambda x: x['time_sum'], reverse=True)[:conf["REPORT_SIZE"]]


def save_report(data, conf):
    template_filename = 'report.html'
    rep_dir = conf['REPORT_DIR']
    output_filename = f'{rep_dir}/report-2222.html'  # TODO filename
    with open(template_filename, mode='rt', encoding="utf-8") as fi:
        body = fi.read().replace('$table_json', json.dumps(data, ensure_ascii=False))
    with open(output_filename, mode='wt', encoding="utf-8") as fo:
        fo.write(body)


def apply_config(config, filename):
    print(f'using config "{filename}"')
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
        print(f'config = {config}')
        log_filename = select_filename(conf=config)
        for data in parse(yield_lines(log_filename)):
            push(collector, data)
        report = stat(coll=collector, conf=config)
        save_report(data=report, conf=config)
    except Exception as ex:
        print(f'ВОЗНИКЛО ИСКЛЮЧЕНИЕ: line {sys.exc_info()[2].tb_lineno} "{ex}"')


if __name__ == "__main__":
    main()
