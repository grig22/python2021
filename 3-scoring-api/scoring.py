import hashlib


def get_score(store, phone='', email='', birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        # birthday.strftime("%Y%m%d") if birthday is not None else "",
        birthday if birthday is not None else "",
    ]
    jo = "".join(key_parts)
    key = "uid:" + hashlib.md5(jo.encode()).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    if score := store.cache_get(key) or 0:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    return r if r else []


# import random
#
#
# def get_score(store, phone=None, email=None, birthday=None, gender=None, first_name=None, last_name=None):
#     score = 0
#     if phone:
#         score += 1.5
#     if email:
#         score += 1.5
#     if birthday and gender:
#         score += 1.5
#     if first_name and last_name:
#         score += 0.5
#     return score
#
#
# def get_interests(store, cid):
#     interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
#     return random.sample(interests, 2)
