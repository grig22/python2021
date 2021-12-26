#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
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
    with opener(name, mode='rt') as fd:
        for line in fd:
            yield line


def parse(lines):
    regexp = r'(?P<remote_addr>\S+) .* (?P<request_time>\S+)'
    prog = re.compile(regexp)
    for line in lines:
        result = prog.match(line)
        yield result.groupdict()


def main():
    data = parse(lines(filename()))
    stop = 0
    for d in data:
        print(d)
        stop += 1
        if stop > 5:
            break


if __name__ == "__main__":
    main()
