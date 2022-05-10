from datetime import datetime, timezone, timedelta
import random
import redis
import pickle
import time


def now():
    return datetime.now(tz=timezone.utc)


# TODO вынести в файл конфигурации
config = {
    'MAX_TRY': 2,
}


class Store:
    def __init__(self):
        self.MAX_TRY = config['MAX_TRY']
        self.magic_seconds = 1
        self.redis = None

    def get_redis_instance(self):
        first_time = True
        while True:  #L25
            try:
                if first_time:
                    first_time = False
                    backoff = 4 * self.magic_seconds
                    print(f'Connecting in {backoff} seconds')
                    time.sleep(backoff)  #L29
                if not self.redis:
                    self.redis = redis.Redis(host='localhost', port=6379)  #L31
                if self.redis.ping():
                    return
            except:
                continue
        self.redis = None

    def try_command(self, f, *args, **kwargs):
        for count in range(0, self.MAX_TRY):
            try:
                backoff = count * self.magic_seconds
                print(f'Trying in {backoff} seconds')
                time.sleep(backoff)
                self.get_redis_instance()
                return f(*args, **kwargs)
            except redis.ConnectionError:
                pass

    def cache_get(self, key):  # FIXME 5
        self.get_redis_instance()
        if not self.redis or not (score := self.try_command(self.redis.get, key)):
            return None
        else:
            return pickle.loads(score)

    def cache_set(self, key, score, ttl):
        self.get_redis_instance()
        if not self.redis:
            return None
        self.try_command(self.redis.set, name=key, value=pickle.dumps(score), ex=ttl)

    def get(self, cid):
        self.get_redis_instance()
        if not self.redis:
            return None
        if not (inte := self.try_command(self.redis.get, cid)):  # они не пересекаются
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
            inte = random.sample(interests, 2)
            self.try_command(self.redis.set, cid, pickle.dumps(inte))
        else:
            inte = pickle.loads(inte)
        return inte


"""
FIXME
+ 0. test.py - это не юнит тесты, скорее функциональные
+ 1. L31 - настройки типа хоста, порта, таймаута и прочего тоже должны прокидываться сюда
+ 2. L25 - с самим редисом стоит пытаться соединиться пока не получится, а вот получать из него что-то можно и retry'ями
+ 3. L29 - перед первым разом спать не стоит, наверное
4. нужно добавить юнит тесты и интеграционные тесты с храналищем
--> хотелось бы узнать более развёрнуто, какие именно тесты добавить, и что они должны тестировать
"""
