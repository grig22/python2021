#!/usr/bin/python3.9

# https://iximiuz.com/ru/posts/writing-python-web-server-part-3/
import socket
import http  # TODO return codes


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
            # print('-------------> serve_forever finally')
            serv_sock.close()
            # OSError: [Errno 98] Address already in use
            # serv_sock.shutdown(socket.SHUT_RDWR)
            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use/4466035#4466035


    def serve_client(self, conn):
        try:
            req = self.parse_request(conn)
            resp = self.handle_request(req)
            self.send_response(conn, resp)
        except ConnectionResetError:
            # conn = None  # TODO зачем это
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
        print('host --->', f'"{host}"')
        if not host:
            raise HTTPError(400, 'Bad request', 'Host header is missing')
        # как-нибудь потом
        # print('????', self._server_name)
        # print('????', f'{self._server_name}:{self._port}')
        # if host not in (self._server_name, f'{self._server_name}:{self._port}'):
        #     raise HTTPError(404, 'Not found')

        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise HTTPError(400, 'Bad request', 'Request line is too long')
        req_line = str(raw, 'utf-8')
        words = req_line.split()
        print('words --->', words)
        if len(words) != 3:
            raise HTTPError(400, 'Bad request', 'Malformed request line')
        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise HTTPError(505, 'HTTP Version Not Supported')
        if method not in ['GET', 'HEAD']:
            raise HTTPError(405, 'Only GET or HEAD Supported')
        return method, target, ver

    def parse_headers(self, rfile):
        headers = dict()
        while True:
            line = rfile.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise HTTPError(494, 'Request header too large')
            if line in (b'\r\n', b'\n', b''):
                break
            # print('line --->', line)
            dec = line.decode('utf-8')
            # print('dec  --->', dec)
            key, _, val = dec.partition(':')
            if val:
                headers[key] = val.strip()
                # print(f'head ---> "{key}" "{headers[key]}"')
            if len(headers) > MAX_HEADERS:
                raise HTTPError(494, 'Too many headers')
            # print('-----------------')
        return headers

    def handle_request(self, req):
        # if req.path == '/users' and req.method == 'POST':
        #     return self.handle_post_users(req)
        #
        # if req.path == '/users' and req.method == 'GET':
        #     return self.handle_get_users(req)
        #
        # if req.path.startswith('/users/'):
        #     user_id = req.path[len('/users/'):]
        #     if user_id.isdigit():
        #         return self.handle_get_user(req, user_id)

        raise HTTPError(404, 'Not found')

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
                body = (err.body or err.reason).encode('utf-8')
            else:
                status = 500
                reason = b'Internal Server Error'
                body = str(err).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(conn, resp)



class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile

    @property
    def path(self):
        return self.url.path

  # @property
  # @lru_cache(maxsize=None)
  # def query(self):
  #   return parse_qs(self.url.query)
  #
  # @property
  # @lru_cache(maxsize=None)
  # def url(self):
  #   return urlparse(self.target)
  #
  # def body(self):
  #   size = self.headers.get('Content-Length')
  #   if not size:
  #     return None
  #   return self.rfile.read(size)

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
        # print('-----------> except KeyboardInterrupt')
        pass
