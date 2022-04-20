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
        for count in range(0, self.MAX_TRY):
            try:
                backoff = count * self.magic_seconds
                print(f'Connecting in {backoff} seconds')
                time.sleep(backoff)
                if not self.redis:
                    self.redis = redis.Redis()
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

+ 0. тесты стоит структурировать так, как в описании ДЗ указано

+ 1. зависимости лучше бы, конечно, через poetry оформлять и конкретные версии указывать

2. запусков тестов стоит настроить через github actions

+ 3. L13 - конфиг захардкожен, инстанс редиса никак не настроен, red - слишком минималистичное имя в данном контексте)

+ 4. L31 - у redis есть свой механизм expire

+ 5. L26 - по заданию cache_get должен быть "отказоустойчивым", не возвращать ошибок, если с хранилищем что-то не так

В моём задании сказано:
Обратите внимание, фунĸции get_score не важна доступность store'а, она использует его ĸаĸ ĸэш 
и, следовательно, должна работать даже если store сгорел в верхних слоях атмосферы.

Этот механизм и реализован в функции 3-scoring-api/scoring.py:4 def get_score
if score := store.cache_get(key) or 0:
    return score

+ 6. не хватает механизма повторных попыток в хранилище
"""
