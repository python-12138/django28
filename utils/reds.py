import redis

conn = redis.Redis(host='127.0.0.1',port=6379,encoding='utf-8')

conn.set('19975083819',9999,ex=10)

value=conn.get('19975083819')

print(value)