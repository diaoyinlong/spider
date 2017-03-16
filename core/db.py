import pymysql


class DB:
    '''
    mysql数据库操作类
    '''

    def __init__(self, hostname, username, password, dbname, port=3306, charset='UTF8'):
        '''初始化数据库连接'''
        self.conn = pymysql.connect(host=hostname, port=port, user=username,
                                    passwd=password, database=dbname, charset=charset)
        self.cur = self.conn.cursor()

    def version(self):
        '''获取mysql版本信息'''
        self.cur.execute('select version();')
        return self.cur.fetchone()

    def ping(self):
        '''检查数据库连接是否存活'''
        return self.conn.ping()

    def insert(self, dataDic, table, isAutoCommit=True, isDebug=False):
        '''添加
        @param dataDic: 要插入的数据字典，字典类型，例：{"id":1, "name":"aaaaaaaa", "pubDate":"2016-10-20"}
        @param table: 目标表，字符串类型，例："test"  
        @param isAutoCommit: 是否自动提交，布尔型，默认为True即插入后立即生效，如果使用事务此值应为False
        @param isDebug:  是否开启调试，布尔型，此值为False时，打印sql语句并return，不执行sql
        '''
        sql = 'INSERT INTO ' + table + ' ('
        for key in dataDic.keys():
            sql = sql + key + ','
        sql = sql.rstrip(',')
        sql = sql + ') values ('
        for value in dataDic.values():
            sql = sql + "'" + str(value).replace('\'', '\'\'') + "',"
        sql = sql.rstrip(',')
        sql = sql + ');'
        if isDebug == True:
            print(sql)
            return
        self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return self.cur.lastrowid

    def insertBySql(self, sql, isAutoCommit=True, isDebug=False):
        '''添加（通过sql）'''
        if isDebug == True:
            print(sql)
            return
        self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return self.cur.lastrowid

    def update(self, dataDic, whereList, table, isAutoCommit=True, isDebug=False):
        '''更新
        @param dataDic: 要插入的数据字典，字典类型，例：{"name":"aaaaaaaa", "pubDate":"2016-10-20"}
        @param whereList: 更新条件，列表类型，例：[{"id":1}, {"k":"pid", "v":"222", "s":">"}]，列表由字典组成，
                          kvs结构中k为键名、v为键值、s为键名与键值关系，如果不是kvs结构，则默认为=关系 
        @param table: 目标表，字符串类型，例："test"  
        @param isAutoCommit: 是否自动提交，布尔型，默认为True即插入后立即生效，如果使用事务此值应为False
        @param isDebug:  是否开启调试，布尔型，此值为False时，打印sql语句并return，不执行sql
        '''
        sql = "UPDATE " + table + " SET "
        for key, value in dataDic.items():
            sql = sql + key + "='" + str(value).replace('\'', '\'\'') + "',"
        sql = sql.rstrip(',')
        sql = sql + " WHERE "
        whereSql = ''
        for item in whereList:
            if not isinstance(item, dict):
                continue
            if 'k' in item and 'v' in item and 's' in item:
                whereSql = whereSql + " AND " + item['k'] + item['s'] + "'" + str(item['v']).replace('\'', '\'\'') + "'"
            else:
                for key, value in item.items():
                    whereSql = whereSql + " AND " + key + "='" + str(value).replace('\'', '\'\'') + "'"
        sql = sql + whereSql.lstrip(" AND")
        if isDebug == True:
            print(sql)
            return
        affectedRowsNum = self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return affectedRowsNum

    def updateBySql(self, sql, isAutoCommit=True, isDebug=False):
        '''更新（通过sql）'''
        if isDebug == True:
            print(sql)
            return
        affectedRowsNum = self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return affectedRowsNum

    def delete(self, whereList, table, isAutoCommit=True, isDebug=False):
        '''删除
        @param whereList: 更新条件，列表类型，例：[{"id":1}, {"k":"pid", "v":"222", "s":">"}]，列表由字典组成，
                          kvs结构中k为键名、v为键值、s为键名与键值关系，如果不是kvs结构，则默认为=关系 
        @param table: 目标表，字符串类型，例："test"  
        @param isAutoCommit: 是否自动提交，布尔型，默认为True即插入后立即生效，如果使用事务此值应为False
        @param isDebug:  是否开启调试，布尔型，此值为False时，打印sql语句并return，不执行sql
        '''
        sql = "DELETE FROM " + table + " WHERE "
        whereSql = ''
        for item in whereList:
            if not isinstance(item, dict):
                continue
            if 'k' in item and 'v' in item and 's' in item:
                whereSql = whereSql + " AND " + item['k'] + item['s'] + "'" + str(item['v']).replace('\'', '\'\'') + "'"
            else:
                for key, value in item.items():
                    whereSql = whereSql + " AND " + key + "='" + str(value).replace('\'', '\'\'') + "'"
        sql = sql + whereSql.lstrip(" AND")
        if isDebug == True:
            print(sql)
            return
        affectedRowsNum = self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return affectedRowsNum

    def deleteBySql(self, sql, isAutoCommit=True, isDebug=False):
        '''删除（通过sql）'''
        if isDebug == True:
            print(sql)
            return
        affectedRowsNum = self.cur.execute(sql)
        if isAutoCommit == True:
            self.conn.commit()
        return affectedRowsNum

    def getone(self, sql):
        '''查询一个，返回一个单值，没有时返回None'''
        self.cur.execute(sql)
        result = self.cur.fetchone()
        if result == None:
            return None
        else:
            return result[0]

    def getrows(self, sql, num=1):
        '''查询一些'''
        self.cur.execute(sql)
        return self.cur.fetchmany(num)

    def getall(self, sql):
        '''查询所有'''
        self.cur.execute(sql)
        return self.cur.fetchall()

    def begin(self):
        '''开启事务'''
        return self.conn.begin()

    def commit(self):
        '''事务提交'''
        return self.conn.commit()

    def rollback(self):
        '''事务回滚'''
        return self.conn.rollback()
