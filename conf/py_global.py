import os
import os.path
import sys
import re
import traceback
import random
import hashlib
import time
import json
import threading
import string
from warnings import catch_warnings

from configparser import ConfigParser
import pycurl

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO
import urllib.request
from urllib.parse import urlparse
from urllib import parse
from PIL import Image
import certifi
from html import parser
from html.parser import HTMLParser
import pymysql
import redis

from core.db import DB
from core.redis import REDIS
from core.curl import *
from core.img_finder import ImgFinder
from core.link_finder import LinkFinder
from core.script_finder import ScriptFinder

# 是否为调试模式
IS_DEBUG = 0

if IS_DEBUG == 0 and len(sys.argv) < 2:
    exit('Please input config file correctly!\nExample:gather.py|process.py dangdang')

ROOT_PATH = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]

# 设置采集环境并加载全局配置文件   local=>本地    neibu=>内部    online=>线上
if len(sys.argv) == 3:
    GATHER_ENV = sys.argv[2]
    if GATHER_ENV != 'local' and GATHER_ENV != 'neibu' and GATHER_ENV != 'online':
        exit('Environment setup error.\n')
else:
    GATHER_ENV = 'local'
globalConfFile = os.path.join(ROOT_PATH, 'conf', 'global_' + GATHER_ENV + '.ini')
if not os.path.isfile(globalConfFile):
    exit('Global configuration file[' + globalConfFile + '] not found.\n')

if IS_DEBUG == 1:  # 调试模式
    path = os.path.join(ROOT_PATH, 'conf', 'jingdong.ini')
else:
    path = os.path.join(ROOT_PATH, 'conf', sys.argv[1] + '.ini')

if not os.path.isfile(path):
    exit('Configuration file[' + path + '] not found.\n')

if IS_DEBUG == 1:  # 调试模式
    PART = 'Gather'
else:
    if sys.argv[0].find("gather") >= 0:
        PART = 'Gather'
    elif sys.argv[0].find("process") >= 0:
        PART = 'Process'
    else:
        exit('Unrecognizable file entry.\n')

gcf = ConfigParser()
cf = ConfigParser()

gcf.read(globalConfFile, 'utf-8')
cf.read(path, 'utf-8')

# 工作名称
PROJECT_NAME = cf.get('project', 'name')
# process脚本进行的操作（插入or更新）
ACTION = cf.get('project', 'action')
# 起始页
HOMEPAGE = cf.get('project', 'home_page')
# 线程数
NUMBER_OF_THREADS = cf.getint('setting', 'threads')
# 商品链接匹配正则式
PROD_PATTERN = cf.get('project', 'prod_pattern')
# 分类链接匹配正则式
CAT_PATTERN = cf.get('project', 'cat_pattern')
# 字符集
CHARSET = cf.get('setting', 'charset')
# 链接白名单
WHITE_LIST = cf.get('project', 'white_list')
# 采集链接睡眠时间
GATHER_TIME = cf.getint('limit', 'gather_time')
# 采集链接多次后才睡眠
GATHER_NUM = cf.getint('limit', 'gather_num')
# 处理链接睡眠时间
PROCESS_TIME = cf.getint('limit', 'process_time')
# 处理链接多次后才睡眠
PROCESS_NUM = cf.getint('limit', 'process_num')
# 请求多少次后重启路由
ROUTER_NUM = cf.getint('limit', 'router_num')
# 指定处理程序走成功或失败队列
MODE = cf.getint('setting', 'mode')
# 是否验证商品已采集过
IS_CHECK_PROD = cf.getint('setting', 'is_check_prod')
# 是否验证分类已采集过
IS_CHECK_CAT = cf.getint('setting', 'is_check_cat')
# 已经爬取过的队列最大长度，超过指定数后gather进程休眠
MAX_CRAWLED_QUEUE_LEN = cf.getint('limit', 'max_crawled_queue_len')

# 日志存放路径
if 'log_floder' in cf.options('setting'):
    LOG_FOLDER = cf.get('setting', 'log_folder')
else:
    LOG_FOLDER = gcf.get('setting', 'log_folder')
# 图片文件存放路径
if 'data_floder' in cf.options('setting'):
    DATA_FOLDER = cf.get('setting', 'data_folder')
else:
    DATA_FOLDER = gcf.get('setting', 'data_folder')
# redis配置
if PROJECT_NAME + '_redis' in gcf.sections():
    REDIS_OBJ = REDIS(gcf.get(PROJECT_NAME + '_redis', 'host'), gcf.getint(PROJECT_NAME + '_redis', 'port'),
                      PROJECT_NAME)
else:
    REDIS_OBJ = REDIS(gcf.get('redis', 'host'), gcf.getint('redis', 'port'), PROJECT_NAME)
# 获取DB游标偏移量
DB_OFFSET = gcf.getint('db', 'step')
# 远程接口地址
SITES = {}
for siteKey in gcf.options('sites'):
    SITES[siteKey] = gcf.get('sites', siteKey)
# 是否要定时重启路由
IS_RESTART_ROUTER = gcf.getint('setting', 'is_restart_router')
# 重启路由后进程眨眼时间
ROUTER_SLEEP_TIME = gcf.getint('setting', 'router_sleep_time')

# redis记录采集进程IP
REDIS_KEY_ANTI = "Anti_"
# redis记录已经处理过的分类URL，防止重复处理
REDIS_KEY_CHECK_CAT = "Check_Cat_"
# redis记录已经处理过的单页URL，防止重复处理
REDIS_KEY_CHECK_PROD = "Check_Prod_"
# redis已经爬取过的队列
REDIS_KEY_CRAWLED = "Crawled"
# redis待爬取队列
REDIS_KEY_QUEUED = "Queued"
# redis处理失败队列
REDIS_KEY_FAILED = "Failed"
# redis记录是否等待路由重启
REDIS_KEY_ROUTER_RESTART = "RouterRestart"
# redis记录0.0.0.0IP
REDIS_KEY_IPZERO = 'IpZero'
# redis记录DB游标位置
REDIS_KEY_DB_CURSOR = 'DBCursor'
# redis记录更新失败数据
REDIS_KEY_UPDATE_FAILED = 'UpdateFailed'

from utils.general import *
from core.anti import *
from model.commonModel import *
from core.spider import Spider
