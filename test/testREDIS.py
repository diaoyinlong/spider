import sys
sys.path.append("..")
from core.redis import *

r = REDIS('192.168.1.36', '6369')

print(r.set('test', '111'))
print(r.get('test'))

'''
r2 = REDIS('192.168.1.36', '6369', 'test_')
print(r2.set('test2', '222'))
print(r2.get('test2'))

print(r2.delete('test2'))

print(r.setex('test3', '333', 600))

print(r.ttl('test3'))

print(r.expire('test3', 1000))

print(r.incr('test4', 1))

print(r.decr('test4'))

print(r.exists('test4'))

print(r.rpush('test5_queue', 3))

print(r.llen('test5_queue'))

print(r.lrange('test5_queue', 0, 10))

print(r.ltrim('test5_queue', 0, 2))
'''
