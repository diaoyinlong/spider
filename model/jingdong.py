from conf.py_global import *


class jingdong(CommonModel):
    '''
          京东数据操作类
    '''

    def __init__(self):
        super().__init__()

    # 插入图书信息表
    def insert_to_bookinfo(self, bookinfo_dic):
        '''
        数据入库及图片上传
        '''

        bookinfo_dic['___key'] = SITES['key']
        response = CURL.post(SITES['jingdong_insert_bookinfo'], bookinfo_dic, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr(
                "sourceid : " + str(bookinfo_dic['sourceId']) + " => jingdong_insert_bookinfo : " + self.getErr())
            return -1
        return int(result['bookId'])

    # 获取图书数量
    def get_book_num(self, source_id):
        '''
        根据源ID获取图书数量
        '''
        data = {}
        data['sourceId'] = source_id
        data['___key'] = SITES['key']
        response = CURL.post(SITES['jingdong_get_book_num_by_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("sourceid : " + str(source_id) + " => jingdong_get_book_num_by_sourceid : " + self.getErr())
            return -1
        return int(result['num'])

    # 通过接口获取source id
    def get_source_id(self):
        if REDIS_OBJ.exists(REDIS_KEY_DB_CURSOR) is False:
            REDIS_OBJ.set(REDIS_KEY_DB_CURSOR, 0)
        begin = int(REDIS_OBJ.get(REDIS_KEY_DB_CURSOR))
        REDIS_OBJ.incr(REDIS_KEY_DB_CURSOR, DB_OFFSET)
        end = begin + DB_OFFSET
        data = {'___key': SITES['key'], 'begin': begin, 'end': end}
        response = CURL.post(SITES['jingdong_get_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Cursor " + str(begin) + " => jingdong_get_sourceid : " + self.getErr())
            return -1
        log_process('=====================Update data from id [' + str(begin) + '] => [' + str(
            end) + ']============================')
        return result

    # 通过接口更新源数据
    def update_source_book(self, book_info):
        book_info['___key'] = SITES['key']
        response = CURL.post(SITES['jingdong_update_bookinfo'], book_info, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Error:" + book_info['sourceId'] + " => jingdong_update_bookinfo : " + self.getErr())
            return -1
        return result

    # 源数据入库
    def insert_source_data(self):
        '''
           开始处理京东详情
           '''
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
                    source_id = str(re.search('[0-9]*.html', uri).group(0).split('.')[0])

                    # 验证图书id在数据库是否存在
                    if self.get_book_num(source_id) > 0:
                        log_process("sourceid : " + source_id + " => has exists in db.")
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    # 防屏蔽策略
                    anti_shield()

                    # 获取图书详情数据
                    book_detail_data = json.loads(
                        CURL.get('http://item.m.jd.com/ware/detail.json?wareId=' + source_id).decode(),
                        encoding='utf-8')

                    # 验证是否存在键值isbook
                    if 'isbook' not in book_detail_data.keys():
                        log_error('source id ' + source_id + ' is not book!!!')
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    # 验证是否为图书
                    if book_detail_data['isbook'] is None or book_detail_data['isbook'] is False:
                        log_error('source id ' + source_id + ' is not book!!!')
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    # 验证source_id是否为有效id
                    if book_detail_data['isbook'] is False or source_id != book_detail_data['ware']['wareId']:
                        log_error('source id ' + source_id + ' is not correct')
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    # 获取评价数据
                    book_rate_data = json.loads(CURL.get(
                        'http://sclub.jd.com/comment/productPageComments.action?productId=' + source_id + '&score=0&sortType=3&page=0&pageSize=10').decode(
                        'gbk', 'replace'), encoding='utf-8')

                    # 获取价格数据
                    book_price_data = json.loads(
                        CURL.get('http://p.3.cn/prices/get?skuid=J_' + source_id).decode(), encoding='utf-8')

                    # 获取人气单品的数据
                    book_popular_data = json.loads(CURL.get(
                        'http://diviner.jd.com/diviner?lid=1&lim=6&ec=utf-8&p=104001&sku=' + source_id,
                        cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')

                    # 获取热门推荐数据
                    book_recommend_data = json.loads(
                        CURL.get('http://diviner.jd.com/diviner?lid=1&lim=23&ec=utf-8&p=104006&sku=' + source_id,
                                 cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')

                    # 获取达人选购的数据
                    also_buy_data = json.loads(
                        CURL.get('http://diviner.jd.com/diviner?lid=1&lim=8&ec=utf-8&p=104002&sku=' + source_id,
                                 cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')

                    # 获取看了又看的数据
                    also_view_data = json.loads(
                        CURL.get('http://diviner.jd.com/diviner?lid=1&lim=6&ec=utf-8&p=104000&sku=' + source_id,
                                 cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')

                    # 获取当前商品是否有货
                    m_html = CURL.get('http://item.m.jd.com/product/' + source_id + '.html').decode()
                    stock = re.search('stockState:\'(\w+)', m_html).group(1)
                    if stock == '无货':
                        stockStatus = 0
                    else:
                        stockStatus = 1
                    log_process('sourceid : ' + source_id + ' => JSON data is loaded!')

                    author = ''
                    press = ''
                    pub_date = ''
                    price = ''
                    isbn = ''
                    edition = ''
                    page_num = ''
                    word_num = ''
                    page_size = ''
                    paper = ''
                    binding = ''
                    category = ''
                    img_path = ''
                    img_path___Target = ''
                    relation_prod = ''
                    language = ''
                    tag = ''
                    popular = ''
                    also_view = ''
                    also_buy = ''
                    hot_recommend = ''
                    editor_comment = ''
                    content_intro = ''
                    author_intro = ''
                    directory = ''
                    brand = ''
                    series = ''

                    # 处理图书分类信息并将分类信息入库
                    html = CURL.get(uri).decode(CHARSET, 'replace')
                    cat = re.search('catName: \[.*]', html).group(0)
                    cat = cat.lstrip('catName: [').rstrip(']').split(',')
                    level = 0
                    for s in cat:
                        level += 1
                        s = s.strip('"')
                        category += s + '>'

                    category = category.rstrip('>')

                    # 处理作者数据
                    s = re.search(
                        r'<div class="p-author" id="p-author" clstag="shangpin\|keycount\|product\|zuozhe_3">(\s.*?)</div>',
                        html, re.S)
                    if s is not None:
                        s = s.group(1).strip()
                        s_arr = s.split('</a>')

                        for s in s_arr:
                            if '<a ' in s and '.html">' in s:
                                author += s[:s.index('<a ')] + s[s.index('.html">') + 7:]
                            else:
                                author += s
                    else:
                        author = ''

                    # 处理定价数据
                    for item in book_price_data:
                        price = item['m']

                    # 处理图书基本信息
                    for attr in book_detail_data['ware']['attrs']:
                        if attr['label'] == '出版社':
                            press = attr['value']
                        elif attr['label'] == '出版时间':
                            pub_date = attr['value']
                        elif attr['label'] == 'ISBN':
                            isbn = attr['value']
                        elif attr['label'] == '版次':
                            edition = attr['value']
                        elif attr['label'] == '页数':
                            page_num = attr['value']
                        elif attr['label'] == '字数':
                            word_num = attr['value']
                        elif attr['label'] == '开本':
                            page_size = attr['value']
                        elif attr['label'] == '用纸':
                            paper = attr['value']
                        elif attr['label'] == '包装':
                            binding = attr['value']
                        elif attr['label'] == '丛书名':
                            series = attr['value']
                        elif attr['label'] == '正文语种':
                            language = attr['value']

                    # 处理推荐信息
                    if book_detail_data['ware']['bookAttrs'] is not None:
                        for attr in book_detail_data['ware']['bookAttrs']:
                            if attr['label'] == '编辑推荐':
                                editor_comment = attr['value']
                            elif attr['label'] == '内容简介':
                                content_intro = attr['value']
                            elif attr['label'] == '作者简介':
                                author_intro = attr['value']
                            elif attr['label'] == '目录':
                                directory = attr['value']

                    if book_detail_data['ware']['shopInfo']['shop'] is not None:
                        brand = book_detail_data['ware']['shopInfo']['shop']['name']

                    # 处理系列数据
                    if book_detail_data['ware']['skuColor'] is not None:
                        for item in book_detail_data['ware']['skuColor']:
                            relation_prod += item['skuId'] + ';'

                    # 处理标签数据
                    if book_rate_data['hotCommentTagStatistics'] is not None:
                        for item in book_rate_data['hotCommentTagStatistics']:
                            tag += item['name'] + '(' + str(item['count']) + ')' + ';'

                    # 处理人气单品
                    if book_popular_data['success'] is True:
                        for item in book_popular_data['data']:
                            popular += str(item['sku']) + ';'
                    else:
                        log_error('Failed to loaded popular book data. source_id:' + source_id)

                    # 处理看了又看
                    if also_view_data['success'] is True:
                        for item in also_view_data['data']:
                            also_view += str(item['sku']) + ';'
                    else:
                        log_error('Failed to loaded also view book data. source_id:' + source_id)

                    # 处理达人选购
                    if also_buy_data['success'] is True:
                        for item in also_buy_data['data']:
                            also_buy += str(item['sku']) + ';'
                    else:
                        log_error('Failed to loaded also buy book data. source_id:' + source_id)

                    # 处理热门推荐
                    if book_recommend_data['success'] is True:
                        for item in book_recommend_data['data']:
                            hot_recommend += str(item['sku']) + ';'
                    else:
                        log_error('Failed to loaded recommend book data. source_id:' + source_id)

                    # 存储图片
                    if book_detail_data['ware']['images'] is not None:
                        imgs = book_detail_data['ware']['images']
                        for img in imgs:
                            if '\n' in img['bigpath']:
                                img['bigpath'] = img['bigpath'].split('\n')[0]
                            s = urlparse(img['bigpath'])
                            path = s.scheme + '://' + s.netloc + s.path.replace('/n0/', '/n12/')
                            arr = path.split('/')
                            name = arr[len(arr) - 1]
                            img_path += os.path.join(DATA_FOLDER + PROJECT_NAME, source_id[0:4], name) + ';'
                            img_path___Target += os.path.join(PROJECT_NAME, source_id[0:4], name) + ';'
                            create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                            save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), path)
                    else:
                        log_error('There is no img to download. source_id:' + source_id)
                    log_process("sourceid : " + source_id + ' => Picture is saved local!')

                    # 验证是否为合格数据
                    verify = bool(category) and \
                             bool(book_detail_data['ware']['wname']) and \
                             bool(author) and \
                             bool(price) and \
                             bool(img_path) and \
                             bool(press) and \
                             bool(isbn) and \
                             bool(edition) and \
                             bool(pub_date) and \
                             bool(content_intro) and \
                             bool(author_intro)

                    # 插入图书数据
                    book_dic = {
                        'sourceId': source_id,
                        'bookName': book_detail_data['ware']['wname'],
                        'author': author,
                        'press': press,
                        'pubDate': pub_date,
                        'price': price,
                        'isbn': isbn,
                        'edition': edition,
                        'pageNum': page_num,
                        'wordNum': word_num,
                        'pageSize': page_size,
                        'usedPaper': paper,
                        'binding': binding,
                        'series': series,
                        'category': category,
                        'imgPath': {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                        'relationProduct': relation_prod,
                        'brand': brand,
                        'language': language,
                        'tag': tag,
                        'popularItem': popular,
                        'alsoView': also_view,
                        'alsoBuy': also_buy,
                        'hotRecommend': hot_recommend,
                        'goodRatePercent': book_rate_data['productCommentSummary']['goodRate'] if book_rate_data[
                                                                                                      'jwotestProduct'] is not None else '',
                        'goodRateCount': book_rate_data['productCommentSummary']['goodCount'] if book_rate_data[
                                                                                                     'jwotestProduct'] is not None else '',
                        'editorComment': editor_comment,
                        'contentIntroduction': content_intro,
                        'authorIntroduction': author_intro,
                        'directory': directory,
                        'crawledTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'isQualified': int(verify),
                        'stock': stockStatus,
                        '___cat_text': category
                    }

                    # 插入图书信息数据
                    result = self.insert_to_bookinfo(book_dic)
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
                try:
                    assoc_arr = self.get_source_id()
                except Exception as e:
                    log_error(str(e))
                    traceback.print_exc()
                    continue

                for v in assoc_arr:
                    source_id_arr.append(v['sourceId'])

            if MODE == 0:
                while REDIS_OBJ.exists(REDIS_KEY_UPDATE_FAILED):
                    source_id_arr.append(pop_from_redis(REDIS_KEY_UPDATE_FAILED))

            if MODE == 2:
                with open('dirty_data', 'rb+') as f:
                    for line in f:
                        source_id_arr.append(line.decode().replace('|', '').strip())
                    f.truncate(0)

            if len(source_id_arr) == 0:
                exit('Update finished^_^')
            else:
                for source_id in source_id_arr:
                    try:
                        # 防屏蔽策略
                        anti_shield()

                        # # 获取图书详情数据
                        # book_detail_data = json.loads(
                        #     CURL.get('http://item.m.jd.com/ware/detail.json?wareId=' + source_id).decode(),
                        #     encoding='utf-8')
                        #
                        # # 获取评价数据
                        # book_rate_data = json.loads(CURL.get(
                        #     'http://sclub.jd.com/comment/productPageComments.action?productId=' + source_id + '&score=0&sortType=3&page=0&pageSize=10').decode(
                        #     'gbk', 'replace'), encoding='utf-8')
                        #
                        # 获取价格数据
                        book_price_data = json.loads(
                            CURL.get('http://p.3.cn/prices/get?skuid=J_' + source_id).decode(), encoding='utf-8')

                        # # 获取人气单品的数据
                        # book_popular_data = json.loads(CURL.get(
                        #     'http://diviner.jd.com/diviner?lid=1&lim=6&ec=utf-8&p=104001&sku=' + source_id,
                        #     cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')
                        #
                        # # 获取热门推荐数据
                        # book_recommend_data = json.loads(
                        #     CURL.get('http://diviner.jd.com/diviner?lid=1&lim=23&ec=utf-8&p=104006&sku=' + source_id,
                        #              cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')
                        #
                        # # 获取达人选购的数据
                        # also_buy_data = json.loads(
                        #     CURL.get('http://diviner.jd.com/diviner?lid=1&lim=8&ec=utf-8&p=104002&sku=' + source_id,
                        #              cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')
                        #
                        # # 获取看了又看的数据
                        # also_view_data = json.loads(
                        #     CURL.get('http://diviner.jd.com/diviner?lid=1&lim=6&ec=utf-8&p=104000&sku=' + source_id,
                        #              cookie='__jda=; __jdb=; __jdc=; __jdu=').decode(), encoding='utf-8')

                        # 获取当前商品是否有货
                        # m_html = CURL.get('http://item.m.jd.com/product/' + source_id + '.html').decode()
                        # stock = re.search('stockState:\'(\w+)', m_html).group(1)
                        # if stock == '无货':
                        #     stockStatus = 0
                        # else:
                        #     stockStatus = 1
                        log_process('sourceid : ' + source_id + ' => JSON data is loaded!')

                        # author = ''
                        # press = ''
                        # pub_date = ''
                        price = ''
                        # isbn = ''
                        # edition = ''
                        # page_num = ''
                        # word_num = ''
                        # page_size = ''
                        # paper = ''
                        # binding = ''
                        # category = ''
                        # img_path = ''
                        # img_path___Target = ''
                        # relation_prod = ''
                        # language = ''
                        # tag = ''
                        # popular = ''
                        # also_view = ''
                        # also_buy = ''
                        # hot_recommend = ''
                        # editor_comment = ''
                        # content_intro = ''
                        # author_intro = ''
                        # directory = ''
                        # brand = ''
                        # series = ''
                        #
                        # # 处理图书分类信息并将分类信息入库
                        # html = CURL.get('http://item.jd.com/' + source_id + '.html').decode(CHARSET, 'replace')
                        # cat = re.search('catName: \[.*]', html).group(0)
                        # cat = cat.lstrip('catName: [').rstrip(']').split(',')
                        # level = 0
                        # for s in cat:
                        #     level += 1
                        #     s = s.strip('"')
                        #     category += s + '>'
                        #
                        # category = category.rstrip('>')
                        #
                        # # 处理作者数据
                        # s = re.search(
                        #     r'<div class="p-author" id="p-author" clstag="shangpin\|keycount\|product\|zuozhe_3">(\s.*?)</div>',
                        #     html, re.S)
                        # if s is not None:
                        #     s = s.group(1).strip()
                        #     s_arr = s.split('</a>')
                        #
                        #     for s in s_arr:
                        #         if '<a ' in s and '.html">' in s:
                        #             author += s[:s.index('<a ')] + s[s.index('.html">') + 7:]
                        #         else:
                        #             author += s
                        # else:
                        #     author = ''
                        #
                        # 处理定价数据
                        for item in book_price_data:
                            price = item['m']
                        #
                        # # 处理图书基本信息
                        # for attr in book_detail_data['ware']['attrs']:
                        #     if attr['label'] == '出版社':
                        #         press = attr['value']
                        #     elif attr['label'] == '出版时间':
                        #         pub_date = attr['value']
                        #     elif attr['label'] == 'ISBN':
                        #         isbn = attr['value']
                        #     elif attr['label'] == '版次':
                        #         edition = attr['value']
                        #     elif attr['label'] == '页数':
                        #         page_num = attr['value']
                        #     elif attr['label'] == '字数':
                        #         word_num = attr['value']
                        #     elif attr['label'] == '开本':
                        #         page_size = attr['value']
                        #     elif attr['label'] == '用纸':
                        #         paper = attr['value']
                        #     elif attr['label'] == '包装':
                        #         binding = attr['value']
                        #     elif attr['label'] == '丛书名':
                        #         series = attr['value']
                        #     elif attr['label'] == '正文语种':
                        #         language = attr['value']
                        #
                        # # 处理推荐信息
                        # if book_detail_data['ware']['bookAttrs'] is not None:
                        #     for attr in book_detail_data['ware']['bookAttrs']:
                        #         if attr['label'] == '编辑推荐':
                        #             editor_comment = attr['value']
                        #         elif attr['label'] == '内容简介':
                        #             content_intro = attr['value']
                        #         elif attr['label'] == '作者简介':
                        #             author_intro = attr['value']
                        #         elif attr['label'] == '目录':
                        #             directory = attr['value']
                        #
                        # if book_detail_data['ware']['shopInfo']['shop'] is not None:
                        #     brand = book_detail_data['ware']['shopInfo']['shop']['name']
                        #
                        # # 处理系列数据
                        # if book_detail_data['ware']['skuColor'] is not None:
                        #     for item in book_detail_data['ware']['skuColor']:
                        #         relation_prod += item['skuId'] + ';'
                        #
                        # # 处理标签数据
                        # if book_rate_data['hotCommentTagStatistics'] is not None:
                        #     for item in book_rate_data['hotCommentTagStatistics']:
                        #         tag += item['name'] + '(' + str(item['count']) + ')' + ';'
                        #
                        # # 处理人气单品
                        # if book_popular_data['success'] is True:
                        #     for item in book_popular_data['data']:
                        #         popular += str(item['sku']) + ';'
                        # else:
                        #     log_error('Failed to loaded popular book data. source_id:' + source_id)
                        #
                        # # 处理看了又看
                        # if also_view_data['success'] is True:
                        #     for item in also_view_data['data']:
                        #         also_view += str(item['sku']) + ';'
                        # else:
                        #     log_error('Failed to loaded also view book data. source_id:' + source_id)
                        #
                        # # 处理达人选购
                        # if also_buy_data['success'] is True:
                        #     for item in also_buy_data['data']:
                        #         also_buy += str(item['sku']) + ';'
                        # else:
                        #     log_error('Failed to loaded also buy book data. source_id:' + source_id)
                        #
                        # # 处理热门推荐
                        # if book_recommend_data['success'] is True:
                        #     for item in book_recommend_data['data']:
                        #         hot_recommend += str(item['sku']) + ';'
                        # else:
                        #     log_error('Failed to loaded recommend book data. source_id:' + source_id)
                        #
                        # # 存储图片
                        # if book_detail_data['ware']['images'] is not None:
                        #     imgs = book_detail_data['ware']['images']
                        #     for img in imgs:
                        #         if '\n' in img['bigpath']:
                        #             img['bigpath'] = img['bigpath'].split('\n')[0]
                        #         s = urlparse(img['bigpath'])
                        #         path = s.scheme + '://' + s.netloc + s.path.replace('/n0/', '/n12/')
                        #         arr = path.split('/')
                        #         name = arr[len(arr) - 1]
                        #         img_path += os.path.join(DATA_FOLDER + PROJECT_NAME, source_id[0:4], name) + ';'
                        #         img_path___Target += os.path.join(PROJECT_NAME, source_id[0:4], name) + ';'
                        #         create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                        #         save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), path)
                        # else:
                        #     log_error('There is no img to download. source_id:' + source_id)
                        # log_process("sourceid : " + source_id + ' => Picture is saved local!')
                        #
                        # # 验证是否为合格数据
                        # verify = bool(category) and \
                        #          bool(book_detail_data['ware']['wname']) and \
                        #          bool(author) and \
                        #          bool(price) and \
                        #          bool(img_path) and \
                        #          bool(press) and \
                        #          bool(isbn) and \
                        #          bool(edition) and \
                        #          bool(pub_date) and \
                        #          bool(content_intro) and \
                        #          bool(author_intro)

                        # 更新图书数据
                        book_dic = {
                            'sourceId': source_id,
                            # 'bookName': book_detail_data['ware']['wname'],
                            # 'author': author,
                            # 'press': press,
                            # 'pubDate': pub_date,
                            'price': price,
                            # 'isbn': isbn,
                            # 'edition': edition,
                            # 'pageNum': page_num,
                            # 'wordNum': word_num,
                            # 'pageSize': page_size,
                            # 'usedPaper': paper,
                            # 'binding': binding,
                            # 'series': series,
                            # 'category': category,
                            # 'imgPath': {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                            # 'relationProduct': relation_prod,
                            # 'brand': brand,
                            # 'language': language,
                            # 'tag': tag,
                            # 'popularItem': popular,
                            # 'alsoView': also_view,
                            # 'alsoBuy': also_buy,
                            # 'hotRecommend': hot_recommend,
                            # 'goodRatePercent': book_rate_data['productCommentSummary']['goodRate'] if book_rate_data[
                            #                                                                               'jwotestProduct'] is not None else '',
                            # 'goodRateCount': book_rate_data['productCommentSummary']['goodCount'] if book_rate_data[
                            #                                                                              'jwotestProduct'] is not None else '',
                            # 'editorComment': editor_comment,
                            # 'contentIntroduction': content_intro,
                            # 'authorIntroduction': author_intro,
                            # 'directory': directory,
                            # 'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                            # 'isQualified': int(verify),
                            # 'stock': stockStatus,
                            'flag': 1
                        }
                        result = self.update_source_book(book_dic)
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
