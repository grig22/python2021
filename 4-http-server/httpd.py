#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# https://iximiuz.com/ru/posts/writing-python-web-server-part-3/

# http://localhost:8080/httptest/wikipedia_russia.html

import os
import socket
from http import HTTPStatus as hs
import urllib.parse
import threading

# todo DOCUMENT_ROOT задается аргументом ĸомандной строĸи -r  # FIXME 1
DOCUMENT_ROOT = os.path.abspath('/home/user/python2021/4-http-server/http-test-suite')

MAX_LINE = 64*1024
MAX_HEADERS = 100


class MyHTTPServer:  # FIXME 5
    def __init__(self, host, port):
        self._host = host
        self._port = port
        # self._server_name = server_name
        # self._users = {}

    def serve_forever(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # в этом стоит разобраться
        try:
            serv_sock.bind((self._host, self._port))
            serv_sock.listen()
            while True:
                conn, _ = serv_sock.accept()
                try:
                    t = threading.Thread(target=self.serve_client, args=(conn,))
                    t.start()  # Запуск нового потока
                    # TODO limit https://stackoverflow.com/questions/19369724/the-right-way-to-limit-maximum-number-of-threads-running-at-once
                    # self.serve_client(conn)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()
            # OSError: [Errno 98] Address already in use
            # https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use/4466035#4466035

    def serve_client(self, conn):
        try:
            request = self.parse_request(conn)
            response = self.handle_request(request)
            self.send_response(conn, response)
        # except ConnectionResetError:
        #     return
        except Exception as e:
            self.send_error(conn, e)
        else:
            request.rfile.close()
        conn.close()

    def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        target = urllib.parse.unquote(target)
        target, _, _ = target.partition('?')
        headers = self.parse_headers(rfile)
        host = headers.get('Host')
        if not host:
            raise HTTPError(hs.BAD_REQUEST, 'Host header is missing')
        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise HTTPError(hs.BAD_REQUEST, 'Request line is too long')
        req_line = str(raw, 'utf-8')
        words = req_line.split()
        if len(words) != 3:
            raise HTTPError(hs.BAD_REQUEST, 'Malformed request line')
        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise HTTPError(hs.BAD_REQUEST, 'HTTP Version Not Supported')
        if method not in ['GET', 'HEAD']:
            raise HTTPError(hs.METHOD_NOT_ALLOWED, 'Only GET or HEAD Supported')
        return method, target, ver

    def parse_headers(self, rfile):
        headers = dict()
        while True:
            line = rfile.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise HTTPError(hs.BAD_REQUEST, 'Request header too large')
            if line in (b'\r\n', b'\n', b''):
                break
            dec = line.decode('utf-8')
            key, _, val = dec.partition(':')
            if val:
                headers[key] = val.strip()
            if len(headers) > MAX_HEADERS:
                raise HTTPError(hs.BAD_REQUEST, 'Too many headers')
        return headers

    def get_file(self, target, size_only):
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
        ct_map = {  # FIXME 3
            # 'html': 'text/html; charset=utf-8',
            # 'js': 'text/javascript; charset=utf-8',
            # 'css': 'text/css; charset=utf-8',
            'html': 'text/html',
            'js': 'text/javascript',
            'css': 'text/css',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'swf': 'application/x-shockwave-flash',
            'txt': 'text/plain; charset=utf-8',
        }
        _, _, ext = target.rpartition('.')
        ct = ct_map.get(ext.lower())
        if not ct:
            raise HTTPError(hs.BAD_REQUEST, 'Invalid MIME type')
        filename = os.path.abspath(f'{DOCUMENT_ROOT}/{target}')
        if DOCUMENT_ROOT not in filename:
            raise HTTPError(hs.FORBIDDEN, 'Document root escape')
        try:
            if not size_only:
                # вычитываем весь файл
                with open(filename, 'rb') as fd:
                    body = fd.read()
                    length = len(body)
            else:
                # получаем только размер
                body = ''
                length = os.path.getsize(filename)
        except:
            raise HTTPError(hs.NOT_FOUND, f'File not found: "{filename}"')
        headers = [('Content-Type', ct),
                   ('Content-Length', length)]
        return Response(hs.OK, 'OK', headers, body)

    def get_dir(self, target):
        dirname = os.path.abspath(f'{DOCUMENT_ROOT}/{target}')
        if DOCUMENT_ROOT not in dirname:
            raise HTTPError(hs.FORBIDDEN, 'Document root escape')
        try:
            ls = os.listdir(dirname)
        except:
            raise HTTPError(hs.NOT_FOUND, f'Dir not found: "{dirname}"')
        body = '<html><head></head><body>'
        for filename in ls:
            body += f'{filename}<br/>'
        body += '</body></html>'
        body = body.encode('utf-8')
        headers = [('Content-Type', 'text/html; charset=utf-8'),
                   ('Content-Length', len(body))]
        return Response(hs.OK, 'OK', headers, body)

    def handle_request(self, request):
        target = request.target
        for ind in ['/', '/index.html']:
            if target.endswith(ind):
                return self.get_dir(target[:-len(ind)])
        return self.get_file(target=target, size_only=(request.method == 'HEAD'))

    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('utf-8'))

        # Отвечать следующими заголовĸами для успешных GET-запросов:
        # Date, Server, Content-Length, Content-Type, Connection
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
        resp.headers.append(('Connection', 'keep-alive'))
        resp.headers.append(('Date', 'Wed, 21 Oct 2015 07:28:00 GMT'))
        resp.headers.append(('Server', 'Apache/2.4.1 (Unix)'))

        if resp.headers:
            for (key, value) in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('utf-8'))

        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()

    def send_error(self, conn, err):
        try:
            if isinstance(err, HTTPError):
                status = err.status
                reason = err.reason
                body = reason.encode('utf-8')
            else:
                status = 500
                reason = 'Internal Server Error'
                body = str(err).encode('utf-8')
        except:
            status = 500
            reason = 'Fatal Internal Server Error'
            body = b'Unknown Internal Server Error'
        resp = Response(status=status, reason=reason,
                        headers=[('Content-Type', 'text/html; charset=utf-8'),
                                 ('Content-Length', len(body))],
                        body=body)
        self.send_response(conn, resp)


class HTTPError(Exception):
    def __init__(self, status, reason):
        super()
        self.status = status
        self.reason = reason
        # self.body = body


class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


if __name__ == '__main__':
    g_host = 'localhost'
    g_port = 8080

    serv = MyHTTPServer(g_host, g_port)
    try:
        print('STARTING SERVER', g_host, g_port)
        serv.serve_forever()
    except KeyboardInterrupt:
        pass


# 0. нет результатов нагрузочного теста
# 1. L13 - я бы, конечно, предпочле смотреть готовые ДЗ
# 2. по заданию еще должны быть воркеры
# 3. L106 - давайте использовать модуль mimetypes
# + 4. L52 - в случае head запроса не надо вычитывать файл в память вообще
# 5. L20 - получился божественный класс, который делает все на свете
# https://melevir.medium.com/короче-говоря-принцип-единой-ответсвенности-92840ac55baa
# + 6. L160 - pep8

# ещё посмотреть
# File "/home/user/python2021/4-http-server/http-test-suite/httptest.py", line 40, in test_directory_index
#     self.assertEqual(int(length), 34)
# AssertionError: 68 != 34
# File "/home/user/python2021/4-http-server/http-test-suite/httptest.py", line 49, in test_index_not_found
#     self.assertEqual(int(r.status), 404)
# AssertionError: 200 != 404
