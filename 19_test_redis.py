import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

try:
    response = r.ping()
    print("Redis connection successful:", response)
except Exception as e:
    print("Redis connection FAILED:", e)
    