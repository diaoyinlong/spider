import json
from core.db import DB
from urllib.parse import urlencode
from conf.py_global import CURL

'''
create table source_zto (id int(10) not null auto_increment, start varchar(50) not null comment '始发地', end varchar(50) not null comment '目的地', weightPrice varchar(10) not null comment '首重价格', addPrice varchar(10) not null comment '续重价格', primary key(id))engine=innodb default charset=utf8;
'''
db = DB('192.168.1.34', 'kfz', 'kongfz.com', 'express')

province = ['黑龙江', '天津', '内蒙古', '上海', '河南', '湖南', '广西', '重庆', '福建', '江西', '青海', '西藏', '陕西', '甘肃', '山东', '浙江', '湖北',
            '新疆', '海南', '北京', '辽宁', '安徽', '云南', '山西', '广东', '宁夏', '河北', '贵州', '江苏', '吉林', '四川']

for i1 in range(len(province)):
    for i2 in range(len(province)):
        post_data = {
            'code': 'undefined',
            'dispProv': province[i2],
            'dispCity': 'x',
            'sendProv': province[i1],
            'sendCity': 'x',
            'weight': '2',
            '_': '1482485209289'
        }
        data = CURL.get(
            'http://www.zto.com/GuestService/GetPrice?' + urlencode(post_data)).decode()
        json_data = json.loads(data)
        weight_price = json_data['Data']['firstMoney']
        add_price = float(json_data['Data']['price']) - float(json_data['Data']['firstMoney'])
        db_data = {'start': province[i1],
                   'end': province[i2],
                   'weightPrice': weight_price,
                   'addPrice': add_price}
        print(db.insert(db_data, 'source_zto'))
pass
