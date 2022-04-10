from datetime import datetime, timezone, timedelta
import random
import redis


def now():
    return datetime.now(tz=timezone.utc)


class Store:
    def __init__(self):
        # self.score_cache = dict()
        self.interests = dict() ########
        self.MAX_TRY = 10
        self.red = None

    def getred(self):
        if not self.red:
            for i in range(self.MAX_TRY):
                try:
                    self.red = redis.Redis()
                    ping = self.red.ping()
                    if ping:
                        return self.red
                except:
                    continue
        return self.red

    def cache_get(self, key):
        if not self.getred() or not (score := self.getred().get(key)):
            return None
        if score['created'] + score['ttl'] < now():
            self.red.delete(key)
            return None
        return score['score']

    def cache_set(self, key, score, ttl):
        if not self.getred():
            return None
        val = {
            'score': score,
            'ttl': timedelta(seconds=ttl),
            'created': now(),
        }
        self.red.set(key, val)

    def get(self, cid):
        if cid not in self.interests:
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
            self.interests[cid] = random.sample(interests, 2)
        return self.interests[cid]
