#!/usr/bin/python3.9

# https://iximiuz.com/ru/posts/writing-python-web-server-part-3/
import socket
from http import HTTPStatus as hs

# todo DOCUMENT_ROOT задается аргументом ĸомандной строĸи -r
DOCUMENT_ROOT = '/home/user/repo/python2021/4-http-server/http-test-suite'

MAX_LINE = 64*1024
MAX_HEADERS = 100


class MyHTTPServer:
    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._users = {}

    def serve_forever(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # в этом стоит разобраться
        try:
            serv_sock.bind((self._host, self._port))
            serv_sock.listen()
            while True:
                conn, _ = serv_sock.accept()
                try:
                    self.serve_client(conn)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()
            # OSError: [Errno 98] Address already in use
            # https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use/4466035#4466035

    def serve_client(self, conn):
        try:
            req = self.parse_request(conn)
            resp = self.handle_request(req)
            self.send_response(conn, resp)
        except ConnectionResetError:
            return
        except Exception as e:
            self.send_error(conn, e)
        else:
            req.rfile.close()
        conn.close()

    def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
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

    def return_file(self, req):
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
        ct_map = {
            'html': 'text/html; charset=utf-8',
            'css': 'text/css; charset=utf-8',
            'js': 'text/javascript; charset=utf-8',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'swf': 'application/x-shockwave-flash',
        }
        _, _, ext = req.target.rpartition('.')
        contentType = ct_map.get(ext.lower())
        if not contentType:
            raise HTTPError(hs.BAD_REQUEST, 'Invalid MIME type')
        with open(f'{DOCUMENT_ROOT}/{req.target}', 'rb') as fd:
            body = fd.read()
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(hs.OK, hs.OK.phrase, headers, body)



    def handle_request(self, req):
        return self.return_file(req)




    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('utf-8'))

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
                reason = b'Internal Server Error'
                body = str(err).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Fatal Internal Server Error'
        resp = Response(status, reason, [('Content-Length', len(body))], body)
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
    g_name = 'AAAA'

    serv = MyHTTPServer(g_host, g_port, g_name)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass
