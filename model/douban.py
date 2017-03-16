from conf.py_global import *


class douban(CommonModel):
    '''
          豆瓣数据操作类
    '''

    def __init__(self):
        super().__init__()

    def get_booknum_with_source_id(self, sourceId):
        '''
        根据源ID获取图书数量
        '''
        data = {}
        data['sourceId'] = sourceId
        data['___key'] = SITES['key']
        response = CURL.post(SITES['douban_get_book_num_by_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(sourceId) + " => douban_get_book_num_by_sourceid : " + self.getErr())
            return -1
        return int(result['num'])

    def insert_bookinfo(self, bookinfo):
        '''
        数据入库及图片上传
        '''
        bookinfo['___key'] = SITES['key']
        response = CURL.post(SITES['douban_insert_bookinfo'], bookinfo, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(bookinfo['sourceId']) + " => douban_insert_bookinfo : " + self.getErr())
            return -1
        return int(result['bookId'])

    # 通过接口获取source id
    def get_source_id(self):
        if REDIS_OBJ.exists(REDIS_KEY_DB_CURSOR) is False:
            REDIS_OBJ.set(REDIS_KEY_DB_CURSOR, 0)
        begin = int(REDIS_OBJ.get(REDIS_KEY_DB_CURSOR))
        REDIS_OBJ.incr(REDIS_KEY_DB_CURSOR, DB_OFFSET)
        end = begin + DB_OFFSET
        data = {'___key': SITES['key'], 'begin': begin, 'end': end}
        response = CURL.post(SITES['douban_get_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Cursor " + str(begin) + " => douban_get_sourceid : " + self.getErr())
            return -1
        log_process('=====================Update data from id [' + str(begin) + '] => [' + str(
            end) + ']============================')
        return result

    # 通过接口更新源数据
    def update_source_book(self, book_info):
        book_info['___key'] = SITES['key']
        response = CURL.post(SITES['douban_update_bookinfo'], book_info, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Error:" + book_info['sourceId'] + " => douban_update_bookinfo : " + self.getErr())
            return -1
        return result

    # 源数据入库
    def insert_source_data(self):
        while True:
            status, uri = parse_url()
            if status == -1:
                log_process("list is null...")
                time.sleep(10)
                continue
            if status == -2:
                log_process("current url is exists,continue...")
                continue
            if status == -3:
                log_process("redis may be there is something wrong with the connection,continue...")
                time.sleep(10)
                continue
            if uri == '':
                log_process("current url is category,continue...")
                continue
            else:
                try:
                    # 防屏蔽策略
                    anti_shield()
                    source_id = re.search(r'https://book.douban.com/subject/(.*)/', uri).group(1)
                    exist_id = self.get_booknum_with_source_id(source_id)
                    if exist_id < 0:
                        log_error(self.getErr())
                        continue
                    elif exist_id > 0:
                        log_process("sourceid : " + source_id + " => has exists in db.")
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    html = CURL.get(uri, referer='https://book.douban.com/tag/').decode()

                    # 获取豆瓣isbn
                    result = re.search(r'<div id="info" class="">(.*?)</div>', html, re.S).group(1)
                    isbn = re.search(r'<span class="pl">ISBN:</span>(.*)<br/>', result)
                    if isbn is None:
                        continue
                    isbn = isbn.group(1).strip()
                    # 获取豆瓣api数据
                    api_data = CURL.get('https://api.douban.com/v2/book/isbn/' + isbn).decode()
                    api_data = json.loads(api_data, encoding='utf-8')

                    # 解析译者
                    translator = ''
                    if len(api_data['translator']) != 0:
                        for item in api_data['translator']:
                            translator += item + ';'
                        translator = translator.rstrip(';')

                    # 解析作者
                    author = ''
                    if len(api_data['author']) != 0:
                        for item in api_data['author']:
                            author += item + ';'
                        author = author.rstrip(';')

                    # 解析列出的其它版本
                    result = re.search(r'<li class="mb8 pl">(.*?)</div>', html, re.S)
                    if result is None:
                        other_version = ''
                    else:
                        other_version = ''
                        other_version_arr = result.group(1).strip().split('</a>')
                        for item in other_version_arr:
                            temp = re.search(r'<a href="https://book.douban.com/subject/(.*)/">', item)
                            if temp is None:
                                continue
                            else:
                                other_version += temp.group(1).strip() + ';'
                        other_version = other_version.rstrip(';')

                    # 豆列推荐
                    result = re.search(r'<div id="db-doulist-section" class="indent">(.*)</div>', html, re.S)
                    if result is None:
                        dou_list = ''
                    else:
                        result = result.group(1)
                        dou_list_arr = result.split('</li>')
                        dou_list = ''
                        for item in dou_list_arr:
                            item = re.search(
                                r'<a class="" href="https://www.douban.com/doulist/(.*)/" target="_blank">',
                                item)
                            if item is None:
                                continue
                            else:
                                item = item.group(1)
                                dou_list += item + ';'
                        dou_list = dou_list.rstrip(';')

                    # 下载图片
                    img = api_data['images']['large']
                    arr = img.split('/')
                    name = arr[len(arr) - 1]
                    img_path = os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name)
                    img_path___Target = os.path.join(PROJECT_NAME, source_id[0:4], name)
                    create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                    save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), img)

                    # 标签
                    tags = ''
                    tag_data = api_data['tags']
                    for item in tag_data:
                        tags += item['name'] + ';'
                    tags = tags.rstrip(';')

                    # 喜欢也喜欢
                    result = re.search(r'<div id="db-rec-section" class="block5 subject_show knnlike">(.*?)</div>',
                                       html,
                                       re.S)
                    if result is None:
                        also_like = ''
                    else:
                        also_like = ''
                        result = result.group(1).strip()
                        also_like_arr = result.split('</dl>')
                        for item in also_like_arr:
                            item = re.search(r'<a href="https://book.douban.com/subject/(.*)/" onclick=".*">', item)
                            if item is None:
                                continue
                            else:
                                item = item.group(1)
                                also_like += item + ';'
                        also_like = also_like.rstrip(';')

                    # 比价
                    result = re.search(r'<ul class="bs noline more-after ">(.*?)</ul>', html, re.S)
                    if result is None:
                        price_compare = ''
                    else:
                        price_compare = ''
                        result = result.group(1)
                        arr = result.split('</li>')
                        for item in arr:
                            n = re.search(r'<div class="basic-info">\s.*<span class="">(.*)</span>', item)
                            p = re.search(r'<span class="buylink-price">\s.*<span class="">\s(.*)', item)
                            if n is None or p is None:
                                continue
                            n = n.group(1).strip()
                            p = p.group(1).strip()
                            price_compare += n + '|' + p + ';'
                        price_compare = price_compare.rstrip(';')

                    is_qualified = bool(api_data['title']) and \
                                   bool(api_data['isbn13']) and \
                                   bool(api_data['author']) and \
                                   bool(api_data['price']) and \
                                   bool(api_data['publisher']) and \
                                   bool(api_data['pubdate']) and \
                                   bool(img_path) and \
                                   bool(api_data['rating']['average']) and \
                                   bool(api_data['catalog']) and \
                                   bool(tags)

                    # 格式化装订字段
                    binding_list = ['精装', '平装', 'Hardcover']
                    binding = ''
                    for item in binding_list:
                        if item not in api_data['binding']:
                            continue
                        else:
                            if item == 'Hardcover':
                                binding = '精装'
                            else:
                                binding = item

                    data_dic = {
                        'sourceId': source_id,
                        'bookName': api_data['title'],
                        'author': author,
                        'press': api_data['publisher'],
                        'subTitle': api_data['subtitle'],
                        'foreignName': api_data['origin_title'],
                        'translator': translator,
                        'pubDate': api_data['pubdate'],
                        'pageNum': api_data['pages'],
                        'price': api_data['price'],
                        'binding': binding,
                        'series': api_data['series']['id'] if 'series' in api_data.keys() else '',
                        'isbn': api_data['isbn13'],
                        'avgRate': api_data['rating']['average'],
                        'rateNum': api_data['rating']['numRaters'],
                        'contentIntroduction': api_data['summary'],
                        'authorIntroduction': api_data['author_intro'],
                        'otherVersion': other_version,
                        'douList': dou_list,
                        'imgPath': {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                        'tag': tags,
                        'directory': api_data['catalog'],
                        'alsoLike': also_like,
                        'priceCompare': price_compare,
                        'crawledTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'isQualified': int(is_qualified),
                        '___cat_text': tags
                    }
                    log_process("sourceid : " + source_id + ' => Call the remote interface to store data...')
                    result = self.insert_bookinfo(data_dic)
                    if result < 0:
                        log_error("sourceid : " + source_id + ' => saved in DB failure.')
                        log_error(self.getErr())
                    else:
                        log_process(
                            "sourceid : " + source_id + ' => saved in DB success. the saved bookid is ' + str(
                                result) + '\n\n\n\n\n')
                        # 入库完毕后将uri存放到Check hash Redis队列
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')

                except Exception as e:
                    log_error("Exception:" + uri + '\t' + str(e))
                    traceback.print_exc()
                    REDIS_OBJ.rpush(REDIS_KEY_FAILED, uri)
                    uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                    IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                    continue

    # 更新源数据
    def update_source_data(self):
        while True:
            source_id_arr = []
            if MODE == 1:
                assoc_arr = self.get_source_id()
                for v in assoc_arr:
                    source_id_arr.append(v['sourceId'])

            if MODE == 0:
                while REDIS_OBJ.exists(REDIS_KEY_UPDATE_FAILED):
                    source_id_arr.append(pop_from_redis(REDIS_KEY_UPDATE_FAILED))
            if len(source_id_arr) == 0:
                REDIS_OBJ.set(REDIS_KEY_DB_CURSOR, 0)
                exit('Update finished^_^')
            else:
                try:
                    for source_id in source_id_arr:
                        # 防屏蔽策略
                        anti_shield()
                        html = CURL.get('https://book.douban.com/subject/' + source_id + '/',
                                        referer='https://book.douban.com/tag/').decode()

                        # 获取豆瓣isbn
                        result = re.search(r'<div id="info" class="">(.*?)</div>', html, re.S).group(1)
                        isbn = re.search(r'<span class="pl">ISBN:</span>(.*)<br/>', result)
                        if isbn is None:
                            continue
                        isbn = isbn.group(1).strip()
                        # 获取豆瓣api数据
                        api_data = CURL.get('https://api.douban.com/v2/book/isbn/' + isbn).decode()
                        api_data = json.loads(api_data, encoding='utf-8')

                        # 解析译者
                        translator = ''
                        if len(api_data['translator']) != 0:
                            for item in api_data['translator']:
                                translator += item + ';'
                            translator = translator.rstrip(';')

                        # 解析作者
                        author = ''
                        if len(api_data['author']) != 0:
                            for item in api_data['author']:
                                author += item + ';'
                            author = author.rstrip(';')

                        # 解析列出的其它版本
                        result = re.search(r'<li class="mb8 pl">(.*?)</div>', html, re.S)
                        if result is None:
                            other_version = ''
                        else:
                            other_version = ''
                            other_version_arr = result.group(1).strip().split('</a>')
                            for item in other_version_arr:
                                temp = re.search(r'<a href="https://book.douban.com/subject/(.*)/">', item)
                                if temp is None:
                                    continue
                                else:
                                    other_version += temp.group(1).strip() + ';'
                            other_version = other_version.rstrip(';')

                        # 豆列推荐
                        result = re.search(r'<div id="db-doulist-section" class="indent">(.*)</div>', html, re.S)
                        if result is None:
                            dou_list = ''
                        else:
                            result = result.group(1)
                            dou_list_arr = result.split('</li>')
                            dou_list = ''
                            for item in dou_list_arr:
                                item = re.search(
                                    r'<a class="" href="https://www.douban.com/doulist/(.*)/" target="_blank">',
                                    item)
                                if item is None:
                                    continue
                                else:
                                    item = item.group(1)
                                    dou_list += item + ';'
                            dou_list = dou_list.rstrip(';')

                        # 下载图片
                        img = api_data['images']['large']
                        arr = img.split('/')
                        name = arr[len(arr) - 1]
                        img_path = os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name)
                        img_path___Target = os.path.join(PROJECT_NAME, source_id[0:4], name)
                        create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                        save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), img)

                        # 标签
                        tags = ''
                        tag_data = api_data['tags']
                        for item in tag_data:
                            tags += item['name'] + ';'
                        tags = tags.rstrip(';')

                        # 喜欢也喜欢
                        result = re.search(r'<div id="db-rec-section" class="block5 subject_show knnlike">(.*?)</div>',
                                           html,
                                           re.S)
                        if result is None:
                            also_like = ''
                        else:
                            also_like = ''
                            result = result.group(1).strip()
                            also_like_arr = result.split('</dl>')
                            for item in also_like_arr:
                                item = re.search(r'<a href="https://book.douban.com/subject/(.*)/" onclick=".*">', item)
                                if item is None:
                                    continue
                                else:
                                    item = item.group(1)
                                    also_like += item + ';'
                            also_like = also_like.rstrip(';')

                        # 比价
                        result = re.search(r'<ul class="bs noline more-after ">(.*?)</ul>', html, re.S)
                        if result is None:
                            price_compare = ''
                        else:
                            price_compare = ''
                            result = result.group(1)
                            arr = result.split('</li>')
                            for item in arr:
                                n = re.search(r'<div class="basic-info">\s.*<span class="">(.*)</span>', item)
                                p = re.search(r'<span class="buylink-price">\s.*<span class="">\s(.*)', item)
                                if n is None or p is None:
                                    continue
                                n = n.group(1).strip()
                                p = p.group(1).strip()
                                price_compare += n + '|' + p + ';'
                            price_compare = price_compare.rstrip(';')

                        is_qualified = bool(api_data['title']) and \
                                       bool(api_data['isbn13']) and \
                                       bool(api_data['author']) and \
                                       bool(api_data['price']) and \
                                       bool(api_data['publisher']) and \
                                       bool(api_data['pubdate']) and \
                                       bool(img_path) and \
                                       bool(api_data['rating']['average']) and \
                                       bool(api_data['catalog']) and \
                                       bool(tags)

                        # 格式化装订字段
                        binding_list = ['精装', '平装', 'Hardcover']
                        binding = ''
                        for item in binding_list:
                            if item not in api_data['binding']:
                                continue
                            else:
                                if item == 'Hardcover':
                                    binding = '精装'
                                else:
                                    binding = item

                        data_dic = {
                            'sourceId': source_id,
                            'bookName': api_data['title'],
                            'author': author,
                            'press': api_data['publisher'],
                            'subTitle': api_data['subtitle'],
                            'foreignName': api_data['origin_title'],
                            'translator': translator,
                            'pubDate': api_data['pubdate'],
                            'pageNum': api_data['pages'],
                            'price': api_data['price'],
                            'binding': binding,
                            'series': api_data['series']['id'] if 'series' in api_data.keys() else '',
                            'isbn': api_data['isbn13'],
                            'avgRate': api_data['rating']['average'],
                            'rateNum': api_data['rating']['numRaters'],
                            'contentIntroduction': api_data['summary'],
                            'authorIntroduction': api_data['author_intro'],
                            'otherVersion': other_version,
                            'douList': dou_list,
                            'imgPath': {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                            'tag': tags,
                            'directory': api_data['catalog'],
                            'alsoLike': also_like,
                            'priceCompare': price_compare,
                            'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                            'isQualified': int(is_qualified),
                            'flag': 1
                        }
                        result = self.update_source_book(data_dic)
                        if result is True:
                            log_process('\t' + source_id + ' => update successful.\n\n\n\n\n')
                        else:
                            log_process('\t' + source_id + ' => update failed!!!\n\n\n\n\n')
                            REDIS_OBJ.rpush(REDIS_KEY_UPDATE_FAILED, source_id)

                except Exception as e:
                    log_error("Exception:" + source_id + '\t' + str(e))
                    traceback.print_exc()
                    REDIS_OBJ.rpush(REDIS_KEY_UPDATE_FAILED, source_id)
                    continue
