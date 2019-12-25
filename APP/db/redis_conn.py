import redis


def init():
    pool = redis.ConnectionPool(host='39.108.180.201', port=6379, password='123456', decode_responses=True)
    return redis.Redis(connection_pool=pool)
