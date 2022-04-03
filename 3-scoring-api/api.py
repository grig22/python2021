#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

import json
from datetime import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from scoring import get_score, get_interests
# https://docs.python.org/3/library/http.html
from http import HTTPStatus as hs

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
ERRORS = {
    hs.BAD_REQUEST: "Bad Request",
    hs.FORBIDDEN: "Forbidden",
    hs.NOT_FOUND: "Not Found",
    hs.UNPROCESSABLE_ENTITY: "Invalid Request",
    hs.INTERNAL_SERVER_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable


class CharField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, str):
            raise ValidationError('CharField must be str')


class ArgumentsField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError('ArgumentsField must be dict')


class EmailField(CharField):
    def validate(self, payload):
        super().validate(payload)
        if '@' not in payload:
            raise ValidationError('EmailField must contain @')


class PhoneField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, (str, int)):
            raise ValidationError('PhoneField must be str or int')
        payload = str(payload)
        regexp = r'^7\d{10}$'
        if not re.match(regexp, payload):
            raise ValidationError(f'PhoneField must be {regexp}')


class DateField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, str):
            raise ValidationError('DateField must be str')
        regexp = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(regexp, payload):
            raise ValidationError(f'DateField must be {regexp}')


class BirthDayField(DateField):
    def validate(self, payload):
        super().validate(payload)
        tdelta = datetime.now() - datetime.strptime(payload, "%d.%m.%Y")
        max_years = 70
        if tdelta.days > max_years * 365:
            raise ValidationError(f'BirthDayField {max_years} years is too much')


class GenderField(BaseField):
    def validate(self, payload):
        if payload not in GENDERS:
            raise ValidationError(f'GenderField must be in {GENDERS}')


class ClientIDsField(BaseField):
    def validate(self, payload):
        if not isinstance(payload, (list, tuple)):
            raise ValidationError('ClientIDsField must be list or tuple')
        if not all(isinstance(x, int) for x in payload):
            raise ValidationError('ClientIDsField all ids must be int')


class BaseSchema:
    @classmethod
    def validate(cls, body):
        errors = dict()
        for attr, field in vars(cls).items():
            if not isinstance(field, BaseField):
                continue
            if field.required and attr not in body:
                errors[attr] = f'required field missing'
                continue
            if not field.nullable and attr in body and not body[attr]:
                errors[attr] = f'field is null'
                continue
            if attr in body and body[attr]:
                try:
                    field.validate(body[attr])
                except Exception as ex:
                    errors[attr] = f'{ex}'
        if errors:
            raise ValidationError(errors)


class ClientsInterestsRequest(BaseSchema):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseSchema):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    special_fields = ['gender']

    @classmethod
    def special_true(cls, field, value):
        if field == 'gender':
            return value in GENDERS

    @classmethod
    def validate(cls, body):
        super().validate(body)  # можно было склеить с результатами валидации производного класса
        for pair in [('phone', 'email'), ('first_name', 'last_name'), ('gender', 'birthday')]:
            check = True
            for i in range(len(pair)):
                field = pair[i]
                check = bool(check and field in body and
                             (body[field] if field not in cls.special_fields else cls.special_true(field, body[field])))
            if check:
                return
        raise ValidationError('must present one of phone-email, first name-last name, gender-birthday')


class MethodRequest(BaseSchema):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @staticmethod
    def check_auth(account, login, token):
        is_admin = login == ADMIN_LOGIN
        if is_admin:
            key = datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        else:
            key = account + login + SALT
        key = key.encode()
        digest = hashlib.sha512(key).hexdigest()
        if digest == token:
            return is_admin
        else:
            return None


class ValidationError(Exception):
    pass


def online_score(ctx, arguments):
    allowed = {field for field in vars(OnlineScoreRequest) if not field.startswith('__')}
    ctx['has'] = set.intersection(allowed, arguments)
    if ctx['is_admin']:
        return {'score': 42}
    return {'score': get_score(store=None, **arguments)}  # strict валидация получилась из-за kwargs


def clients_interests(ctx, arguments):
    ctx['nclients'] = len(arguments['client_ids'])
    return {cid: get_interests(store=None, cid=cid) for cid in arguments['client_ids']}


def method_handler(request, ctx, store):
    method_map = {
        'online_score': (online_score, OnlineScoreRequest),
        'clients_interests': (clients_interests, ClientsInterestsRequest),
    }
    body = request["body"]
    try:
        MethodRequest.validate(body)
        is_admin = MethodRequest.check_auth(account=body['account'], login=body['login'], token=body['token'])
        if is_admin is None:
            return 'Auth error', hs.FORBIDDEN
        ctx['is_admin'] = is_admin
        method_name = body['method']
        arguments = body['arguments']
        if method_name not in method_map:
            return f'Unknown method: {method_name}', hs.BAD_REQUEST
        method, schema = method_map[method_name]
        schema.validate(arguments)
        return method(ctx=ctx, arguments=arguments), hs.OK
    except ValidationError as ex:
        return f'Validation error: {ex}', hs.UNPROCESSABLE_ENTITY
    except Exception as ex:
        return f'Unknown error {ex}', hs.INTERNAL_SERVER_ERROR


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self):
        return self.headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, hs.OK
        context = {"request_id": self.get_request_id()}
        body = None
        data_string = None
        try:
            if self.headers['Content-Type'] != 'application/json':
                raise Exception('WANT JSON ONLY')
            content_length = int(self.headers['Content-Length'])
            data_string = self.rfile.read(content_length)
            body = json.loads(data_string)
        except Exception as e:
            logging.exception("Parsing error: %s" % e)
            code = hs.BAD_REQUEST

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
                    code = hs.INTERNAL_SERVER_ERROR
            else:
                code = hs.NOT_FOUND

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
