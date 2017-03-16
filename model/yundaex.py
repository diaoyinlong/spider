import json
from core.db import DB
from conf.py_global import CURL

'''
create table source_yundaex (id int(10) not null auto_increment, start varchar(50) not null comment '始发地', end varchar(50) not null comment '目的地', weightPrice varchar(10) not null comment '首重价格', addPrice varchar(10) not null comment '续重价格', primary key(id))engine=innodb default charset=utf8;
'''
db = DB('192.168.1.34', 'kfz', 'kongfz.com', 'express')

province_json_data = CURL.post(
    'http://mobile.yundasys.com:2137/mobileweb/interface.do?member.order_new.getSubListByCode',
    'action=member.order_new.getSubListByCode&version=V1.0&req_time=1482466267794&appid=undefined&openid=undefined&data={"accountId":"","type":"province"}',
    postType=2).decode()
province_json_data = json.loads(province_json_data)

data = province_json_data['body']['data']
province = []
for item in data:
    if item['is_beyond'] == '0':
        continue
    province.append(item['name'])
for i1 in range(len(province)):
    for i2 in range(len(province)):
        post_data1 = {'action': 'member.account.query_freight',
                      'version': 'V1.0',
                      'req_time': '1482465645668',
                      'appid': 'undefined',
                      'openid': 'undefined',
                      'data': '{"startCity":"' + province[i1] + '","endCity":"' + province[
                          i2] + '","weight":"1","type":"1"}'}

        post_data2 = {'action': 'member.account.query_freight',
                      'version': 'V1.0',
                      'req_time': '1482465645668',
                      'appid': 'undefined',
                      'openid': 'undefined',
                      'data': '{"startCity":"' + province[i1] + '","endCity":"' + province[
                          i2] + '","weight":"2","type":"1"}'}

        json_data1 = CURL.post(
            'http://mobile.yundasys.com:2137/mobileweb/interface.do?member.account.query_freight',
            post_data1,
            postType=1).decode()

        json_data2 = CURL.post(
            'http://mobile.yundasys.com:2137/mobileweb/interface.do?member.account.query_freight',
            post_data2,
            postType=1).decode()

        weight_price_json_data1 = json.loads(json_data1)
        weight_price_json_data2 = json.loads(json_data2)

        weight_price = weight_price_json_data1['body']['data']
        add_price = float(weight_price_json_data2['body']['data']) - float(weight_price_json_data1['body']['data'])

        data = {'start': province[i1],
                'end': province[i2],
                'weightPrice': weight_price,
                'addPrice': add_price}

        print(db.insert(data, 'source_yundaex'))
