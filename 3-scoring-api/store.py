from datetime import datetime, timezone, timedelta
import random


def now():
    return datetime.now(tz=timezone.utc)


class Store:

    def __init__(self):
        self.score_cache = dict()
        self.interests = dict()

    def cache_get(self, key):
        score = self.score_cache.get(key)
        if not score:
            return None
        if score['created'] + score['ttl'] < now():
            self.score_cache.pop(key)
            return None
        return score['score']

    def cache_set(self, key, score, ttl):
        self.score_cache[key] = {
            'score': score,
            'ttl': timedelta(seconds=ttl),
            'created': now(),
        }

    def get(self, cid):
        if cid not in self.interests:
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
            self.interests[cid] = random.sample(interests, 2)
        return self.interests[cid]
