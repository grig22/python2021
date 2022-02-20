#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import re

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:  # TODO абстрактный базовый класс
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable


class CharField(BaseField):
    def validate(self, payload):
        return isinstance(payload, str)


class ArgumentsField(BaseField):
    def validate(self, payload):
        return isinstance(payload, dict)


class EmailField(CharField):
    def validate(self, payload):
        if not super().validate(payload):  # TODO это можно бы обобщить
            return False
        return '@' in payload


class PhoneField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, (str, int)):
            return False
        payload = str(payload)  # где же мой const
        regexp = r'^7\d{10}$'
        return bool(re.match(regexp, payload))


class DateField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, str):
            return False
        regexp = r'^\d{2}\.\d{2}\.\d{4}$'
        return bool(re.match(regexp, payload))


class BirthDayField(DateField):
    def validate(self, payload):
        if not super().validate(payload):
            return False
        birth = datetime.datetime.strptime(payload, "%d.%m.%Y")
        tdelta = datetime.datetime.now() - birth
        return tdelta.days <= 365 * 70  # не будем углубляться в летоисчисление


class GenderField(BaseField):
    def validate(self, payload):
        return payload in GENDERS


class ClientIDsField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, (list, tuple)):
            return False
        return all(isinstance(x, int) for x in payload)


class ClientsInterestsRequest(object):
    # client_ids - массив числе, обязательно, не пустое
    client_ids = ClientIDsField(
        required=True,
        nullable=False)

    # date - дата в формате DD.MM. YYYY, опционально, может быть пустым
    date = DateField(
        required=False,
        nullable=True)


class OnlineScoreRequest(object):
    pass
    # first_name - строка, опционально, может быть пустым
    first_name = CharField(
        required=False,
        nullable=True)

    # last_name - строка, опционально, может быть пустым
    last_name = CharField(
        required=False,
        nullable=True)

    # email - строка, в которой есть @, опционально, может быть пустым
    email = EmailField(
        required=False,
        nullable=True)

    # phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
    phone = PhoneField(
        required=False,
        nullable=True)

    # birthday - дата в формате DD.MM. YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
    birthday = BirthDayField(
        required=False,
        nullable=True)

    # gender - число 0, 1 или 2, опционально, может быть пустым
    gender = GenderField(
        required=False,
        nullable=True)
#
#
class MethodRequest(object):
    # account - строка, опционально, может быть пустым
    account = CharField(
        required=False,
        nullable=True)

    # login - строка, обязательно, может быть пустым
    login = CharField(
        required=True,
        nullable=True)

    # token - строка, обязательно, может быть пустым
    token = CharField(
        required=True,
        nullable=True)

    # arguments - словарь (объект в терминах json), обязательно, может быть пустым
    arguments = ArgumentsField(
        required=True,
        nullable=True)

    # method - строка, обязательно, может быть пустым (не может)
    method = CharField(
        required=True,
        nullable=False)
#
#     @property
#     def is_admin(self):
#         return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


class ValidationError(Exception):
    pass


class ExecutionError(Exception):
    pass


def validate(body, schema):
    errors = dict()
    for attr, field in vars(schema).items():
        if attr.startswith('__'):
            continue
        if field.required and attr not in body:
            errors[attr] = f'Required field missing: {attr}'
            continue
        if not field.nullable and attr in body and not body[attr]:
            errors[attr] = f'Field is null: {attr}'
            continue
        if attr in body and body[attr] and not field.validate(body[attr]):
            errors[attr] = f'Field validation failed: {attr}'
            continue
    # присутствует хоть одна пара phone-email, first name-last name, gender-birthday с непустыми значениями.
    if isinstance(schema, OnlineScoreRequest):
        count_pairs = 0
        for pair in [
            ('phone', 'email'),
            ('first_name', 'last_name'),
            ('gender', 'birthday'),
        ]:
            check = True
            for i in range(len(pair)):
                check = check and (pair[i] in body and body[pair[i]])
            if check:
                break
        errors['special'] = 'Missing mandatory pairs'
    if errors:
        raise ValidationError(errors)


def online_score(arguments):
    pass


def clients_interests(arguments):
    return {"1": ["books", "hi-tech"], "2": ["pets", "tv"]}


def method_handler(request, ctx, store):
    # TODO декоратор схемы валидации на каждый метод
    method_map = {
        'online_score': (online_score, OnlineScoreRequest),
        'clients_interests': (clients_interests, OnlineScoreRequest),
    }
    body = request["body"]
    try:
        validate(body, MethodRequest)
        method = body['method']
        arguments = body['arguments']
        if method not in method_map:
            raise ExecutionError(f'Unknown method: {method}')
        method, schema = method_map[method]
        validate(arguments, schema)
        response, code = method(arguments=arguments), 200
    except ValidationError as e:
        response, code = str(e), 422
    except ExecutionError as e:
        response, code = str(e), 400
    except Exception as e:
        response, code = str(e), 500
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self):
        return self.headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id()}
        body = None
        data_string = None
        try:
            if self.headers['Content-Type'] != 'application/json':
                raise Exception('WANT JSON ONLY')
            content_length = int(self.headers['Content-Length'])
            data_string = self.rfile.read(content_length)
            # print('data --->', data_string)
            body = json.loads(data_string)
        except Exception as e:
            logging.exception("Parsing error: %s" % e)
            code = BAD_REQUEST

        if body:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        request={"body": body, "headers": self.headers},
                        ctx=context,
                        store=self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)  # TODO
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
