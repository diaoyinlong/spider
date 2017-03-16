from conf.py_global import *


# Each website is a separate project (folder)
def create_project_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# Create a new file
def write_file(path, data):
    if not os.path.exists(os.path.dirname(path)):
        create_project_dir(os.path.dirname(path))
    with open(path, 'a+') as f:
        f.write(data)


# Add data onto an existing file
def append_to_file(path, data):
    with open(path, 'a') as file:
        file.write(data + '\n')


# Delete the contents of a file
def delete_file_contents(path):
    open(path, 'w').close()


# Save remote picture to local disk
def save_remote_img(path, src):
    with open(path, 'wb') as f:
        f.write(CURL.get(src))


# Read a file and convert each line to set items
def file_to_set(file_name):
    results = set()
    with open(file_name, 'rt') as f:
        for line in f:
            results.add(line.replace('\n', ''))
    return results


# Iterate through a set, each item will be a line in a file
def set_to_file(links, file_name):
    with open(file_name, "w") as f:
        for l in sorted(links):
            f.write(l + "\n")


def push_all_to_redis(key, values):
    '''
    存储数据到redis
    :param key:
    :param values:
    :return:
    '''

    for value in sorted(values):
        REDIS_OBJ.rpush(key, value)


def pop_from_redis(key, direction='l'):
    '''
    pop redis数据并格式化成字符串
    :param key:
    :param direction:
    :return:
    '''
    b = bytes
    if direction == 'l':
        b = REDIS_OBJ.lpop(key)
    if direction == 'r':
        b = REDIS_OBJ.rpop(key)
    if b is None:
        return ''
    return b.decode('utf-8', 'replace')


def write(file, data, isIp=1):
    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    local_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    file_path = os.path.join(LOG_FOLDER, local_date + '_' + PROJECT_NAME + '_' + str(os.getpid()) + '_' + file)
    ip = ""
    if isIp == 1:
        ip = getIp()
    if len(ip) > 0:
        write_file(file_path, local_time + '\t[' + ip + ']' + data + '\n')
        print(local_time + '\t[' + ip + ']' + data + '\n')
    else:
        write_file(file_path, local_time + '\t' + data + '\n')
        print(local_time + '\t' + data + '\n')


def log_error(data, isIp=1):
    write('error.log', data, isIp)


def log_process(data, isIp=1):
    write('process.log', data, isIp)


def log_gather(data, isIp=1):
    write('gather.log', data, isIp)


def log_write(data, isIp=1):
    if PART == 'Gather':
        write('gather.log', data, isIp)
    elif PART == 'Process':
        write('process.log', data, isIp)


def getIp(cache=True):
    '''
        获取IP
    '''
    ip = '0.0.0.0'
    try:
        if cache is True:
            # 每120秒获取当前进程IP一次
            cacheIp = REDIS_OBJ.get(REDIS_KEY_ANTI + str(os.getpid()))
            if cacheIp is None:
                result = json.loads(CURL.post(SITES['get_my_ip'], {'___key': SITES['key']}, agent='kfz-agent').decode())
                ip = result['data']['ip']
                REDIS_OBJ.setex(REDIS_KEY_ANTI + str(os.getpid()), ip, 120)
            else:
                ip = cacheIp.decode()

        if cache is False:
            result = json.loads(CURL.post(SITES['get_my_ip'], {'___key': SITES['key']}, agent='kfz-agent').decode())
            ip = result['data']['ip']

    except Exception as e:
        log_write("Exception:" + '\t [getIp failure] \t' + str(e), isIp=0)
        traceback.print_exc()
    finally:
        return ip

        # try:
        #     if ip == '0.0.0.0':
        #         if REDIS_OBJ.exists(REDIS_KEY_IPZERO, '') > 0:
        #             if REDIS_OBJ.ttl(REDIS_KEY_IPZERO, '') < 300:
        #                 restart_router()
        #                 REDIS_OBJ.delete(REDIS_KEY_IPZERO, '')
        #         else:
        #             REDIS_OBJ.setex(REDIS_KEY_IPZERO, ip, 600, '')
        # except Exception as e:
        #     log_write("Exception:" + '\t [getIp failure] \t' + str(e), isIp=0)
        #     traceback.print_exc()


def restart_router():
    '''
    重启路由
    '''
    if REDIS_OBJ.exists(REDIS_KEY_ROUTER_RESTART) > 0:
        log_write('Wait the router restart...', isIp=0)
        return

    REDIS_OBJ.setex(REDIS_KEY_ROUTER_RESTART, PROJECT_NAME, ROUTER_SLEEP_TIME, '')

    try:
        # 模拟登录获取hash_key和session_id
        loginHeader = CURL.post('http://192.168.168.1/login.cgi',
                                "username=admin&password=f6e6b6df2d&selectLanguage=CH&LANGUAGE=&OKBTN=%E7%99%BB%E5%BD%95",
                                postType=2,
                                agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                                referer="http://192.168.168.1/"
                                , returnType=2
                                , cookie="username=%%"
                                , http_header=[
                'Content-Type: application/x-www-form-urlencoded',
                'Pragma: no-cache',
                'Accept-Encoding: gzip, deflate',
                'Accept-Language: zh-CN',
                'Accept: text/html, application/xhtml+xml, */*',
                "Expect:"
            ]
                                )
        loginHeader = loginHeader.decode('utf-8', 'replace')
        hash_key = re.search('hash_key=(\w+),', loginHeader).group(1)
        session_id = re.search('session_id=(\w+);', loginHeader).group(1)

        # 获取当前ip的wan线路
        interface_status = CURL.get('http://192.168.168.1/interface_status.cgi',
                                    agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
                                    , returnType=0
                                    , cookie="username=%%; hash_key=" + hash_key + ",session_id=" + session_id
                                    )
        interface_status = interface_status.decode('utf-8', 'replace')
        ip = getIp(cache=False)
        connect = ''
        disconnect = ''
        wan = re.search(ip + '.*?<A href=#.*?dev=(\w+)&time=', interface_status, re.S)

        # 连接失败尝试重连
        if wan is None:
            log_write('Rebuild connection!!!', isIp=0)

            loginHeader = CURL.post('http://192.168.168.1/login.cgi',
                                    "username=admin&password=f6e6b6df2d&selectLanguage=CH&LANGUAGE=&OKBTN=%E7%99%BB%E5%BD%95",
                                    postType=2,
                                    agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                                    referer="http://192.168.168.1/"
                                    , returnType=2
                                    , cookie="username=%%"
                                    , http_header=[
                    'Content-Type: application/x-www-form-urlencoded',
                    'Pragma: no-cache',
                    'Accept-Encoding: gzip, deflate',
                    'Accept-Language: zh-CN',
                    'Accept: text/html, application/xhtml+xml, */*',
                    "Expect:"
                ]
                                    )
            loginHeader = loginHeader.decode('utf-8', 'replace')
            hash_key = re.search('hash_key=(\w+),', loginHeader).group(1)
            session_id = re.search('session_id=(\w+);', loginHeader).group(1)

            # 建立连接
            result = CURL.post('http://192.168.168.1/interface_status.cgi',
                               'LANGUAGE=&PWAN2L_OKBTN=%E8%BF%9E%E6%8E%A5WAN2',
                               postType=2,
                               agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                               referer="http://192.168.168.1/"
                               , returnType=2
                               , cookie="username=%%; hash_key=" + hash_key + ",session_id=" + session_id
                               , http_header=[
                    'Content-Type: application/x-www-form-urlencoded',
                    'Pragma: no-cache',
                    'Accept-Encoding: gzip, deflate',
                    'Accept-Language: zh-CN',
                    'Accept: text/html, application/xhtml+xml, */*',
                    "Expect:"
                ]
                               ).decode()
            hash_key = re.search('hash_key=(\w+),', result).group(1)
            session_id = re.search('session_id=(\w+);', result).group(1)
            CURL.post('http://192.168.168.1/interface_status.cgi',
                      'LANGUAGE=&PWAN4L_OKBTN=%E8%BF%9E%E6%8E%A5WAN4',
                      postType=2,
                      agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                      referer="http://192.168.168.1/"
                      , returnType=2
                      , cookie="username=%%; hash_key=" + hash_key + ",session_id=" + session_id
                      , http_header=[
                    'Content-Type: application/x-www-form-urlencoded',
                    'Pragma: no-cache',
                    'Accept-Encoding: gzip, deflate',
                    'Accept-Language: zh-CN',
                    'Accept: text/html, application/xhtml+xml, */*',
                    "Expect:"
                ]
                      )
            log_write('Connection rebuild success!!!', isIp=0)

        else:
            wan = wan.group(1)
            if wan == 'wan2':
                connect = 'LANGUAGE=&PWAN2L_OKBTN=%E8%BF%9E%E6%8E%A5WAN2'
                disconnect = 'LANGUAGE=&PWAN2D_OKBTN=%E6%96%AD%E5%BC%80WAN2'
            if wan == 'wan4':
                connect = 'LANGUAGE=&PWAN4L_OKBTN=%E8%BF%9E%E6%8E%A5WAN4'
                disconnect = 'LANGUAGE=&PWAN4D_OKBTN=%E6%96%AD%E5%BC%80WAN4'

            # 获取hash_key和session_id
            result = CURL.post('http://192.168.168.1/login.cgi',
                               "username=admin&password=f6e6b6df2d&selectLanguage=CH&LANGUAGE=&OKBTN=%E7%99%BB%E5%BD%95",
                               postType=2,
                               agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                               referer="http://192.168.168.1/"
                               , returnType=2
                               , cookie="username=%%"
                               , http_header=[
                    'Content-Type: application/x-www-form-urlencoded',
                    'Pragma: no-cache',
                    'Accept-Encoding: gzip, deflate',
                    'Accept-Language: zh-CN',
                    'Accept: text/html, application/xhtml+xml, */*',
                    "Expect:"
                ]
                               )
            result = result.decode('utf-8', 'replace')

            if '200 OK' in result:
                hash_key = re.search('hash_key=(\w+),', result).group(1)
                session_id = re.search('session_id=(\w+);', result).group(1)

                # 断开连接
                result = CURL.post('http://192.168.168.1/interface_status.cgi',
                                   disconnect,
                                   postType=2,
                                   agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                                   referer="http://192.168.168.1/"
                                   , returnType=2
                                   , cookie="username=%%; hash_key=" + hash_key + ",session_id=" + session_id
                                   , http_header=[
                        'Content-Type: application/x-www-form-urlencoded',
                        'Pragma: no-cache',
                        'Accept-Encoding: gzip, deflate',
                        'Accept-Language: zh-CN',
                        'Accept: text/html, application/xhtml+xml, */*',
                        "Expect:"
                    ]
                                   )

                result = result.decode('utf-8', 'replace')
                if '200 OK' in result:
                    hash_key = re.search('hash_key=(\w+),', result).group(1)
                    session_id = re.search('session_id=(\w+);', result).group(1)

                    # 建立连接
                    result = CURL.post('http://192.168.168.1/interface_status.cgi',
                                       connect,
                                       postType=2,
                                       agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                                       referer="http://192.168.168.1/"
                                       , returnType=2
                                       , cookie="username=%%; hash_key=" + hash_key + ",session_id=" + session_id
                                       , http_header=[
                            'Content-Type: application/x-www-form-urlencoded',
                            'Pragma: no-cache',
                            'Accept-Encoding: gzip, deflate',
                            'Accept-Language: zh-CN',
                            'Accept: text/html, application/xhtml+xml, */*',
                            "Expect:"
                        ]
                                       )
                    if '200 OK' in result.decode('utf-8', 'replace'):
                        log_write('Success restart router...', isIp=0)
                        time.sleep(2)
                    else:
                        log_write('Failed to build connection!!!', isIp=0)
                else:
                    log_write('Failed to disconnect router!!!', isIp=0)
            else:
                log_write('Failed to get router interface status!!!', isIp=0)

    except Exception as e:
        log_write("Exception:" + '\t' + str(e), isIp=0)
        traceback.print_exc()

        # try:
        #     CURL.get(rUrl, authorization=authorization)
        #     result = CURL.get(rrUrl, referer=referer, authorization=authorization).decode('utf-8', 'replace')
        #     if result.find("<TITLE>Router Status</TITLE>") >= 0:
        #         log_write('Router restart success!!!', isIp=0)
        #     else:  # 重试
        #         log_write('Router restart failure!!!', isIp=0)
        #         log_write('Router restart try Again!!!', isIp=0)
        #         if CURL.get(rUrl, authorization=authorization, returnType=1) == 200:
        #             result = CURL.get(rrUrl, referer=referer, authorization=authorization).decode('utf-8', 'replace')
        #             if result.find("<TITLE>Router Status</TITLE>") >= 0:
        #                 log_write('Router restart success!!!', isIp=0)
        #             else:
        #                 log_write('Router restart failure!!!', isIp=0)
        #         else:
        #             log_write('Router restart try failure!!!', isIp=0)
        # except Exception as e:
        #     log_write("Exception:" + '\t' + str(e), isIp=0)
        #     traceback.print_exc()


def parse_url():
    '''
    将商品的url解析出来,并将redis内的category链接存储到Redis
    :return:
    '''

    parsed_uri = ''
    raw_uri = ''
    status = 1
    prod_pattern = re.compile(PROD_PATTERN)
    cat_pattern = re.compile(CAT_PATTERN)

    # 判断从哪个队列取数据
    try:
        if MODE == 1:
            iExistsC = REDIS_OBJ.exists(REDIS_KEY_CRAWLED)
            if iExistsC > 0:
                raw_uri = pop_from_redis(REDIS_KEY_CRAWLED)
            else:
                status = -1
                return status, parsed_uri
        elif MODE == 0:
            iExistsF = REDIS_OBJ.exists(REDIS_KEY_FAILED)
            if iExistsF > 0:
                raw_uri = pop_from_redis(REDIS_KEY_FAILED)
            else:
                status = -1
                return status, parsed_uri

        prod_match = prod_pattern.match(raw_uri)
        url_md5 = hashlib.md5(raw_uri.encode('utf-8')).hexdigest()
        if prod_match:
            parsed_uri = raw_uri
            if IS_CHECK_PROD and REDIS_OBJ.exists(REDIS_KEY_CHECK_PROD + url_md5) and MODE == 1:  # 如果当前链接存在
                status = -2
                return status, parsed_uri

        if parsed_uri != '':
            log_process('********* uri:' + parsed_uri + ' is parsed!')
        return status, parsed_uri
    except Exception as e:
        log_error("Exception:" + '\t' + str(e))
        traceback.print_exc()
        return -3, parsed_uri
