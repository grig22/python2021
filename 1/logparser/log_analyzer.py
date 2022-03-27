#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gzip
import re
import statistics
import json
# import sys
import os
import datetime
import collections
import logging
import argparse

GLOBAL_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "MAX_ERROR_PERCENT": 2,
    "MY_LOG_FILENAME": "my.log",
}

Filename = collections.namedtuple('Filename', 'name date extension')


def split_filenames(names):
    regexp = r'nginx-access-ui\.log-(\d+).?(\S*)'
    prog = re.compile(regexp)
    for name in names:
        try:
            result = prog.match(name)
            date = datetime.datetime.strptime(result.group(1), '%Y%m%d')
            extension = result.group(2)
            if extension not in ['gz', '']:
                continue
        except:
            continue
        else:
            yield Filename(name=name, date=date, extension=extension)


def get_last_log(log_dir):
    logging.info(f'Смотрим логи в каталоге "{log_dir}"')
    if not os.path.isdir(log_dir):
        raise Exception(f'Нету каталога "{log_dir}"')
    if not (names := os.listdir(log_dir)):
        raise Exception(f'Нету логов в каталоге "{log_dir}"')
    fresh = max(split_filenames(names), key=lambda x: x.date)
    logging.info(f'Обнаружен свежий лог "{fresh.name}"')
    return fresh


def yield_lines(filename, extension):
    opener = {'gz': gzip.open}.get(extension, open)
    with opener(filename, mode='rt', encoding="utf-8") as fd:
        for line in fd:
            yield line


def push(collector, data):
    url, time = data
    if url not in collector.keys():
        collector[url] = list()
    collector[url].append(time)


# log_format ui_short
# '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
# '$status $body_bytes_sent "$http_referer" '
# '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
# '$request_time';
def parse_log(collector, text, max_err_perc):
    overall, errors = 0, 0
    regexp = r'(?:\S+\s+){3}\[.+?\]\s+\"\S+\s+(.+?)\s+\S+\".*\s+([\d.]+)$'
    prog = re.compile(regexp)
    for line in text:
        overall += 1
        result = prog.match(line)
        if not result:
            errors += 1
            continue
        push(collector=collector, data=result.group(1, 2))
    err_perc = 100 * errors / overall
    logging.info(f'Обработано строк {overall}, из них ошибочных {errors}, это {err_perc:.2f}%')
    if err_perc > max_err_perc:
        raise Exception(f'Слишком много ошибок {err_perc:.2f}% а можно только {max_err_perc}%')


# "url": "/api/v2/internal/html5/phantomjs/queue/?wait=1m",
# {"count": 2767, - сколько раз встречается URL, абсолютное значение
# "time_avg": 62.994999999999997, - средний $request_time для данного URL'а
# "time_max": 9843.5689999999995, - максимальный $request_time для данного URL'а
# "time_sum": 174306.35200000001, - суммарный $request_time для данного URL'а, абсолютное значение
# "time_med": 60.073, - медиана $request_time для данного URL'а
# "time_perc": 9.0429999999999993, - суммарный $request_time для данного URL'а,
#   в процентах относительно общего $request_time всех запросов
# "count_perc": 0.106}  - сколько раз встречается URL, в процентах относительно общего числа запросов
def calculate_statistics(collector, report_size):
    overall_time = 0.0
    overall_count = 0.0
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
        overall_time += stats['time_sum']
        overall_count += stats['count']
        collector[url] = stats
    # второй проход - когда посчитаны overall
    for url in collector:
        stats = collector[url]
        stats['time_perc'] = 100 * stats['time_sum'] / overall_time
        stats['count_perc'] = 100 * stats['count'] / overall_count
        # kinda post-processing
        for k, v in stats.items():
            if isinstance(v, float):
                stats[k] = round(v, 3)
    return sorted(list(collector.values()), key=lambda x: x['time_sum'], reverse=True)[:report_size]


def save_report(report_data, report_dir, report_fullname):
    os.makedirs(report_dir, exist_ok=True)
    with open('report.html', mode='rt', encoding="utf-8") as fi:
        body = fi.read().replace('$table_json', json.dumps(report_data, ensure_ascii=False))
    with open(report_fullname, mode='wt', encoding="utf-8") as fo:
        fo.write(body)


def merge_config(config, filename):
    if os.path.getsize(filename):
        with open(filename, mode='rt', encoding="utf-8") as ff:
            config.update(json.load(ff))


def main():
    collector = dict()

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--config')
        if args := parser.parse_args():
            merge_config(GLOBAL_CONFIG, args.config)

        logging.basicConfig(
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S',
            level=logging.DEBUG,
            filename=GLOBAL_CONFIG.get('MY_LOG_FILENAME'),
        )

        logging.info('--> Выполнение начато')
        logging.info(f'Параметры конфигурации {GLOBAL_CONFIG}')

        log_dir = GLOBAL_CONFIG['LOG_DIR']
        report_dir = GLOBAL_CONFIG['REPORT_DIR']
        name, date, extension = get_last_log(log_dir)

        log_fullname = f'{log_dir}/{name}'
        report_fullname = f'{report_dir}/report-{date.isoformat().replace("-", ".")}.html'
        if os.path.isfile(report_fullname):
            raise Exception(f'Файл "{report_fullname}" уже существует, всё отменяется')

        logging.info(f'Парсим лог "{log_fullname}"')
        parse_log(collector=collector,
                  text=yield_lines(filename=log_fullname, extension=extension),
                  max_err_perc=GLOBAL_CONFIG['MAX_ERROR_PERCENT'])

        logging.info(f'Считаем статистику')
        report_data = calculate_statistics(collector=collector,
                                           report_size=GLOBAL_CONFIG['REPORT_SIZE'])

        logging.info(f'Пишем отчёт "{report_fullname}"')
        save_report(report_data=report_data,
                    report_dir=report_dir,
                    report_fullname=report_fullname)

        logging.info(f'--> Выполнение завершено')

    except Exception as ex:
        # ei = sys.exc_info()
        # logging.exception(f'ВОЗНИКЛО ИСКЛЮЧЕНИЕ в строке {ei[2].tb_lineno} {ei[0]} {ex}')
        logging.exception(f'ВОЗНИКЛО ИСКЛЮЧЕНИЕ {ex}')

    except:
        logging.exception(f'НЕБЫВАЛОЕ ИСКЛЮЧЕНИЕ')


if __name__ == "__main__":
    main()
