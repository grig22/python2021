from datetime import datetime, timezone, timedelta
import random
import redis
import pickle
import time


def now():
    return datetime.now(tz=timezone.utc)


# TODO вынести в файл конфигурации
config = {
    'MAX_TRY': 10,
}


class Store:
    def __init__(self):
        self.MAX_TRY = config['MAX_TRY']
        self.magic_seconds = 2
        self.redis = None

    def get_redis_instance(self):
        try:
            for count in range(0, self.MAX_TRY):
                backoff = count * self.magic_seconds
                print('Reconnecting in {} seconds'.format(backoff))
                time.sleep(backoff)
                self.redis = self.redis or redis.Redis()
                if self.redis and self.redis.ping():
                    return
        except:
            pass


    def try_command(self, f, *args, **kwargs):
        for count in range(1, self.MAX_TRY + 1):
            try:
                return f(*args, **kwargs)
            except redis.ConnectionError:
                backoff = count * self.magic_seconds
                print('Retrying in {} seconds'.format(backoff))
                time.sleep(backoff)
                self.get_redis_instance()


    def cache_get(self, key):  # FIXME 5
        self.get_redis_instance()
        if not self.redis or not (score := self.try_command(self.redis.get(key))):
            return None
        else:
            return pickle.loads(score)

    def cache_set(self, key, score, ttl):
        redis_instance = self.get_redis_instance()
        if not redis_instance:
            return None
        redis_instance.set(name=key, value=pickle.dumps(score), ex=ttl)

    def get(self, cid):
        redis_instance = self.get_redis_instance()
        if not redis_instance:
            return None
        if not (inte := redis_instance.get(cid)):  # они не пересекаются
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
            inte = random.sample(interests, 2)
            redis_instance.set(cid, pickle.dumps(inte))
        else:
            inte = pickle.loads(inte)
        return inte


"""
FIXME

+ 0. тесты стоит структурировать так, как в описании ДЗ указано

+- 1. зависимости лучше бы, конечно, через poetry оформлять и конкретные версии указывать

2. запусков тестов стоит настроить через github actions

3. L13 - конфиг захардкожен, инстанс редиса никак не настроен, red - слишком минималистичное имя в данном контексте)

+ 4. L31 - у redis есть свой механизм expire

+ 5. L26 - по заданию cache_get должен быть "отказоустойчивым", не возвращать ошибок, если с хранилищем что-то не так

В моём задании сказано:
Обратите внимание, фунĸции get_score не важна доступность store'а, она использует его ĸаĸ ĸэш 
и, следовательно, должна работать даже если store сгорел в верхних слоях атмосферы.

Этот механизм и реализован в функции 3-scoring-api/scoring.py:4 def get_score
if score := store.cache_get(key) or 0:
    return score

6. не хватает механизма повторных попыток в хранилище
"""


    """
    https://stackoverflow.com/questions/24773114/retry-redis-operation-when-connection-is-down
    max_retries = 10
count = 0

r = redis.Redis(host='10.23.*.*', port=6379, db=0)

def try_command(f, *args, **kwargs):
    while True:
        try:
            return f(*args, **kwargs)
        except redis.ConnectionError:
            count += 1

            # re-raise the ConnectionError if we've exceeded max_retries
            if count > max_retries:
                raise

            backoff = count * 5

            print('Retrying in {} seconds'.format(backoff)
            time.sleep(backoff)

            r = redis.Redis(host='10.23.*.*', port=6379, db=0)

# this will retry until a result is returned
# or will re-raise the final ConnectionError
try_command(r.hset, field, keys, 1)
    """