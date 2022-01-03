#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import re

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def filename():
    return 'nginx-access-ui.log-20170630.gz'  # TODO честно выбирать из многих файлов


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
    regexp = r'\S+\s+\S+\s+\S+\s+\[.+?\]\s+\"\S+\s+(.+?)\s+\S+\"\s+.*\s+(\S+)'
    prog = re.compile(regexp)
    for line in text:
        result = prog.match(line)
        yield result.group(1, 2)


def push(collector, data):
    pass


def main():
    collector = dict()
    data = parse(lines(filename()))
    stop = 0
    for d in data:
        print(d)
        stop += 1
        if stop > 5:
            break


if __name__ == "__main__":
    main()