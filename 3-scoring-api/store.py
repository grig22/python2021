from datetime import datetime, timezone, timedelta
import random
import redis
import pickle


def now():
    return datetime.now(tz=timezone.utc)


class Store:
    def __init__(self):
        self.MAX_TRY = 10
        self.red = None

    def getred(self):
        for i in range(self.MAX_TRY):
            try:
                self.red = redis.Redis()
                if self.red.ping():
                    return self.red
            except Exception as ex:
                pass
        return None

    def cache_get(self, key):
        red = self.getred()
        if not red or not (score := red.get(key)):
            return None
        score = pickle.loads(score)
        if score['created'] + score['ttl'] < now():
            red.delete(key)
            return None
        return score['score']

    def cache_set(self, key, score, ttl):
        red = self.getred()
        if not red:
            return None
        val = {
            'score': score,
            'ttl': timedelta(seconds=ttl),
            'created': now(),
        }
        red.set(key, pickle.dumps(val))

    def get(self, cid):
        red = self.getred()
        if not red:
            return None
        if not (inte := red.get(cid)):  # они не пересекаются
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
            inte = random.sample(interests, 2)
            red.set(cid, pickle.dumps(inte))
        else:
            inte = pickle.loads(inte)
        return inte
