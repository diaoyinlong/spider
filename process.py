# encoding: utf-8
from conf.py_global import PROJECT_NAME, ACTION

if PROJECT_NAME is None or PROJECT_NAME not in 'jingdong|dangdang|douban|amazon':
    exit('Please give correct project name in config file!!!')
elif ACTION is None or ACTION not in 'insert|update':
    exit('Please give correct action for processing!!!')
else:
    module = __import__('model.' + PROJECT_NAME, globals(), locals(), [PROJECT_NAME])
    obj = getattr(module, PROJECT_NAME)()
    if ACTION == 'insert':
        obj.insert_source_data()

    if ACTION == 'update':
        obj.update_source_data()
