import sys
sys.path.append("..")
from core.db import *

'''create database booklib2 default charset utf8;'''
db = DB('127.0.0.1', 'root', '', 'booklib2')
print(db.version())
print(db.ping())
''' create table test(id int primary key auto_increment,name varchar(255) not null default '') default charset utf8;'''
# lastid = db.insertBySql("insert into test(name) values('张三');")
# print(lastid)
# affectedRowsNum = db.updateBySql("update test set name='张三三' where id=1;")
# print(affectedRowsNum)
# affectedRowsNum = db.deleteBySql("delete from test where id=2;")
# print(affectedRowsNum)
# num = db.getone("select count(*) from test;")
# print(num)
# someRows = db.getrows("select * from test where id>10;", 10)
# print(someRows)
# rows = db.getall("select * from test;")
# print(rows)

# '''测试事务回滚'''
# db.begin()
# lastid = db.insertBySql("insert into test(name) values('张三');", False)
# print(lastid)
# affectedRowsNum = db.updateBySql("update test set name='张三三' where id="+lastid+";", False)
# print(affectedRowsNum)
# if lastid>0 and affectedRowsNum>0:
#     db.commit()
# else:
#     db.rollback()
# 
# '''测试事务提交'''
# db.begin()
# lastid = db.insertBySql("insert into test(name) values('张三');", False)
# print(lastid)
# affectedRowsNum = db.updateBySql("update test set name='张三三' where id='"+str(lastid)+"';", False)
# print(affectedRowsNum)
# if lastid>0 and affectedRowsNum>0:
#     db.commit()
# else:
#     db.rollback()

db.insert({"id":1, "name":"aaaaaaaa", "pubDate":"2016-10-20"}, 'test', isDebug = True)
db.update({"name":"aaaaaaaa", "pubDate":"2016-10-20"}, [{"id":1}, {"k":"pid", "v":"222", "s":">"}], 'test', isDebug = True)
db.delete([{"id":1}, {"k":"pid", "v":"222", "s":">"}], 'test', isDebug = True)
print(db.getone("select count(*) from test;"))
print(db.getone("select id from test where name='张三三'"))
print(db.getall("select * from test where id>40 limit 2,2"))



