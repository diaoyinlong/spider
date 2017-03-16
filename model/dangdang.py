from conf.py_global import *


class dangdang(CommonModel):
    '''
          当当数据操作类
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
        response = CURL.post(SITES['dangdang_get_book_num_by_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(sourceId) + " => dangdang_get_book_num_by_sourceid : " + self.getErr())
            return -1
        return int(result['num'])

    def insert_bookinfo(self, bookinfo):
        '''
        数据入库及图片上传
        '''
        bookinfo['___key'] = SITES['key']
        response = CURL.post(SITES['dangdang_insert_bookinfo'], bookinfo, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(bookinfo['sourceId']) + " => dangdang_insert_bookinfo : " + self.getErr())
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
        response = CURL.post(SITES['dangdang_get_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Cursor " + str(begin) + " => dangdang_get_sourceid : " + self.getErr())
            return -1
        log_process('=====================Update data from id [' + str(begin) + '] => [' + str(
            end) + ']============================')
        return result

    # 通过接口更新源数据
    def update_source_book(self, book_info):
        book_info['___key'] = SITES['key']
        response = CURL.post(SITES['dangdang_update_bookinfo'], book_info, agent='kfz-agent')
        result = self.formatResponse(response)
        if result is False:
            self.setErr("Error:" + book_info['sourceId'] + " => dangdang_update_bookinfo : " + self.getErr())
            return -1
        return result

    # 源数据入库
    def insert_source_data(self):
        '''
            开始处理当当详情
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
                    if len(source_id) > 8 or (len(source_id) == 8 and source_id[0:1] != '2'):  # 此种商品ID不做处理
                        log_process("current sourceid is invalid,continue...")
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue
                    exist_id = self.get_booknum_with_source_id(source_id)
                    if exist_id < 0:
                        log_error(self.getErr())
                        continue
                    elif exist_id > 0:
                        log_process("sourceid : " + source_id + " => has exists in db.")
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    # 防屏蔽策略
                    anti_shield()

                    m_uri = "http://product.m.dangdang.com/product.php?pid=" + source_id + "&host=product.dangdang.com#ddclick?act=click&pos=" + source_id + "_1_0_p&cat=01.00.00.00.00.00&key=&qinfo=&pinfo=10401671_1_60&minfo=&ninfo=&custid=&permid=20140804102648932240195425284464578&ref=&rcount=&type=&t=" + str(
                        time.time())[0:10] + "000&searchapi_version=test_ori"
                    referer = "http://product.dangdang.com/" + source_id + ".html#ddclick?act=click&pos=" + source_id + "_0_2_p&cat=01.00.00.00.00.00&key=&qinfo=&pinfo=10401671_1_60&minfo=&ninfo=&custid=&permid=20140804102648932240195425284464578&ref=&rcount=&type=&t=" + str(
                        time.time())[0:10] + "000&searchapi_version=test_ori"

                    m_html = CURL.get(m_uri, referer=referer).decode()
                    str_script = re.search('<script type="text/javascript">(.*?)</script>', m_html, re.S).group(0)

                    # 将script解析成JSON
                    str_script_parsed = re.search('\{.+\}', str_script).group(0)
                    data = json.loads(str_script_parsed, encoding='utf-8')

                    # 如果id不一致禁止入库
                    if source_id != data['product_info_new']['product_id']:
                        log_error(
                            'Parsed ID:' + source_id + ' is not equal to JSON ID:' + data['product_info_new'][
                                'product_id'])
                        continue

                    # 判断是否有货
                    s = "<button class='buy big J_add_remind' dd_name='缺货登记'>到货提醒</button>"
                    if s in m_html:
                        stock = 0
                    else:
                        stock = 1

                    # 包含买了又买和看了又看的数据
                    data_1 = json.loads(
                        CURL.get('http://product.dangdang.com/?r=callback%2Frecommend&productId=' + source_id).decode(
                            CHARSET,
                            'replace'),
                        encoding='utf-8')

                    # 包含好评率的数据
                    data_2 = json.loads(
                        CURL.get('http://product.m.dangdang.com/h5ajax.php?action=get_reviews&pid=' + source_id,
                                 referer='http://product.m.dangdang.com/' + source_id + '.html').decode(
                            'utf-8', 'replace'),
                        encoding='utf-8')
                    log_process('sourceid : ' + source_id + ' => JSON data is loaded!')

                    # 拼接图片存储路径
                    img = data['product_info_new']['images_big']
                    img_path = ''
                    img_path___Target = ''
                    for s in img:
                        arr = s.split('/')
                        name = arr[len(arr) - 1]
                        img_path += os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name) + ';'
                        img_path___Target += os.path.join(PROJECT_NAME, source_id[0:4], name) + ';'
                        create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                        save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), s)
                    log_process("sourceid : " + source_id + ' => Picture is saved local!')

                    # 系列
                    relation_product = ''
                    for item in data['relation_product']:
                        if item['product_id'] == source_id:
                            continue
                        relation_product += item['product_id'] + ';'

                    # 买了还买
                    also_buy = ''

                    # 看了还看
                    also_view = ''
                    for field in data_1['data']:
                        if field == 'alsoBuy':
                            for item in data_1['data']['alsoBuy']['list']:
                                if len(item['productId']) > 8 or \
                                        (len(item['productId']) == 8 and item['productId'][0:1] != '2'):
                                    continue
                                also_buy += item['productId'] + ';'

                        if field == 'alsoView':
                            for item in data_1['data']['alsoView']['list']:
                                if len(item['productId']) > 8 or \
                                        (len(item['productId']) == 8 and item['productId'][0:1] != '2'):
                                    continue
                                also_view += item['productId'] + ';'

                    if data['product_info_new']['publish_info']['number_of_pages'] == '':
                        data['product_info_new']['publish_info']['number_of_pages'] = '0'

                    if data['product_info_new']['publish_info']['number_of_words'] == '':
                        data['product_info_new']['publish_info']['number_of_words'] = '0'

                    # 获取分类信息
                    html = CURL.get('http://product.dangdang.com/' + source_id + '.html',
                                    referer='http://category.dangdang.com/cp01.00.00.00.00.00-f0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0.html').decode(
                        CHARSET, 'replace')
                    cat_part = re.search(
                        r'<li class="clearfix fenlei" dd_name="详情所属分类" id="detail-category-path">.*</li>',
                        html).group(
                        0).split('</span><span class="lie">')
                    cat_links = list()
                    for part in cat_part:
                        cat_links.append(re.search(r'<a target.*</a>', part).group(0).split('&gt;'))

                    cat_href_list = list()
                    cat_text_list = list()
                    for links in cat_links:
                        for link in links:
                            cat_href_list.append(link[link.index('http://'):link.index('.html') + 5])
                            cat_text_list.append(link[link.index('>') + 1:link.index('</a>')])

                        cat_href_list.append(';')
                        cat_text_list.append(';')

                    # 拼接分类文本
                    cat_text = ''
                    for s in cat_text_list:
                        cat_text += s + '>'
                    cat_text = cat_text.replace('>;>', ';')
                    cat_href = ''
                    for u in cat_href_list:
                        cat_href += u + '>'
                    cat_href = cat_href.replace('>;>', ';')

                    # 数据入库
                    printing_date = ''
                    for item in data['product_desc_sorted']:
                        if item['name'] == '出版信息':
                            x = item['content']
                            for y in x:
                                if y['name'] == '出版时间':
                                    printing_date = y['content']

                    # 如果必填字段为空 isQualified 字段为0
                    is_qualified = bool(data['product_info_new']['category_info']['book_detail_category']) \
                                   and bool(data['product_info_new']['product_name']) \
                                   and bool(cat_text) \
                                   and bool(data['product_info_new']['publish_info']['author_name']) \
                                   and bool(data['product_info_new']['publish_info']['publisher']) \
                                   and bool(data['product_info_new']['publish_info']['publish_date']) \
                                   and bool(data['product_info_new']['original_price']) \
                                   and bool(img_path) \
                                   and bool(data['product_info_new']['publish_info']['print_copy']) \
                                   and bool(printing_date) \
                                   and bool(data['product_info_new']['publish_info']['version_num']) \
                                   and bool(data['product_info_new']['publish_info']['standard_id']) \
                                   and bool(data['product_desc']['content']) \
                                   and bool(data_2['goodRatio']) \
                                   and bool(also_view)

                    # 插入图书数据
                    data_dic = {"sourceId": data['product_info_new']['product_id'],
                                "bookName": data['product_info_new']['product_name'],
                                "subName": data['product_info_new']['subname'],
                                "author": data['product_info_new']['publish_info']['author_name'],
                                "press": data['product_info_new']['publish_info']['publisher'],
                                "pubDate": data['product_info_new']['publish_info']['publish_date'],
                                "price": data['product_info_new']['original_price'],
                                "isbn": data['product_info_new']['publish_info']['standard_id'],
                                "edition": data['product_info_new']['publish_info']['version_num'],
                                "printingDate": printing_date,
                                "printingNum": data['product_info_new']['publish_info']['print_copy'],
                                "pageNum": data['product_info_new']['publish_info']['number_of_pages'],
                                "wordNum": data['product_info_new']['publish_info']['number_of_words'],
                                "pageSize": data['product_info_new']['publish_info']['product_size'],
                                "usedPaper": data['product_info_new']['publish_info']['paper_quality'],
                                "binding": data['product_info_new']['publish_info']['binding'],
                                "category": data['product_info_new']['category_info']['book_detail_category'],
                                "catNames": cat_text,
                                "imgPath": {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                                "relationProduct": relation_product,
                                "alsoView": also_view,
                                "alsoBuy": also_buy,
                                "goodRatePercent": data_2['goodRatio'],
                                "goodRateCount": data_2['count'],
                                "crawledTime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                "updateTime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                "editorComment": data['product_desc']['abstract'],
                                "contentIntroduction": data['product_desc']['content'],
                                "authorIntroduction": data['product_desc']['authorintro'],
                                "directory": data['product_desc']['catalog'],
                                "isQualified": int(is_qualified),
                                "stock": stock,
                                "___cat_text": cat_text,
                                "___cat_href": cat_href}

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
            if len(source_id_arr) == 0:
                REDIS_OBJ.set(REDIS_KEY_DB_CURSOR, 0)
                exit('Update finished^_^')
            else:
                for source_id in source_id_arr:
                    try:
                        # 防屏蔽策略
                        anti_shield()

                        m_uri = "http://product.m.dangdang.com/product.php?pid=" + source_id + "&host=product.dangdang.com#ddclick?act=click&pos=" + source_id + "_1_0_p&cat=01.00.00.00.00.00&key=&qinfo=&pinfo=10401671_1_60&minfo=&ninfo=&custid=&permid=20140804102648932240195425284464578&ref=&rcount=&type=&t=" + str(
                            time.time())[0:10] + "000&searchapi_version=test_ori"
                        referer = "http://product.dangdang.com/" + source_id + ".html#ddclick?act=click&pos=" + source_id + "_0_2_p&cat=01.00.00.00.00.00&key=&qinfo=&pinfo=10401671_1_60&minfo=&ninfo=&custid=&permid=20140804102648932240195425284464578&ref=&rcount=&type=&t=" + str(
                            time.time())[0:10] + "000&searchapi_version=test_ori"

                        m_html = CURL.get(m_uri, referer=referer).decode()
                        # str_script = re.search('<script type="text/javascript">(.*?)</script>', m_html, re.S).group(0)
                        #
                        # # 将script解析成JSON
                        # str_script_parsed = re.search('\{.+\}', str_script).group(0)
                        # data = json.loads(str_script_parsed, encoding='utf-8')
                        #
                        # # 如果id不一致禁止入库
                        # if source_id != data['product_info_new']['product_id']:
                        #     log_error(
                        #         'Parsed ID:' + source_id + ' is not equal to JSON ID:' + data['product_info_new'][
                        #             'product_id'])
                        #     continue

                        # 判断是否有货
                        s = "<button class='buy big J_add_remind' dd_name='缺货登记'>到货提醒</button>"
                        if s in m_html:
                            stock = 0
                        else:
                            stock = 1

                        # # 包含买了又买和看了又看的数据
                        # data_1 = json.loads(
                        #     CURL.get(
                        #         'http://product.dangdang.com/?r=callback%2Frecommend&productId=' + source_id).decode(
                        #         CHARSET,
                        #         'replace'),
                        #     encoding='utf-8')
                        #
                        # # 包含好评率的数据
                        # data_2 = json.loads(
                        #     CURL.get('http://product.m.dangdang.com/h5ajax.php?action=get_reviews&pid=' + source_id,
                        #              referer='http://product.m.dangdang.com/' + source_id + '.html').decode(
                        #         'utf-8', 'replace'),
                        #     encoding='utf-8')
                        # log_process('sourceid : ' + source_id + ' => JSON data is loaded!')
                        #
                        # # 拼接图片存储路径
                        # img = data['product_info_new']['images_big']
                        # img_path = ''
                        # img_path___Target = ''
                        # for s in img:
                        #     arr = s.split('/')
                        #     name = arr[len(arr) - 1]
                        #     img_path += os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name) + ';'
                        #     img_path___Target += os.path.join(PROJECT_NAME, source_id[0:4], name) + ';'
                        #     create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4]))
                        #     save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[0:4], name), s)
                        # log_process("sourceid : " + source_id + ' => Picture is saved local!')
                        #
                        # # 系列
                        # relation_product = ''
                        # for item in data['relation_product']:
                        #     if item['product_id'] == source_id:
                        #         continue
                        #     relation_product += item['product_id'] + ';'
                        #
                        # # 买了还买
                        # also_buy = ''
                        #
                        # # 看了还看
                        # also_view = ''
                        # for field in data_1['data']:
                        #     if field == 'alsoBuy':
                        #         for item in data_1['data']['alsoBuy']['list']:
                        #             if len(item['productId']) > 8 or \
                        #                     (len(item['productId']) == 8 and item['productId'][0:1] != '2'):
                        #                 continue
                        #             also_buy += item['productId'] + ';'
                        #
                        #     if field == 'alsoView':
                        #         for item in data_1['data']['alsoView']['list']:
                        #             if len(item['productId']) > 8 or \
                        #                     (len(item['productId']) == 8 and item['productId'][0:1] != '2'):
                        #                 continue
                        #             also_view += item['productId'] + ';'
                        #
                        # if data['product_info_new']['publish_info']['number_of_pages'] == '':
                        #     data['product_info_new']['publish_info']['number_of_pages'] = '0'
                        #
                        # if data['product_info_new']['publish_info']['number_of_words'] == '':
                        #     data['product_info_new']['publish_info']['number_of_words'] = '0'
                        #
                        # # 获取分类信息
                        # html = CURL.get('http://product.dangdang.com/' + source_id + '.html',
                        #                 referer='http://category.dangdang.com/cp01.00.00.00.00.00-f0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0%7C0.html').decode(
                        #     CHARSET, 'replace')
                        # cat_part = re.search(
                        #     r'<li class="clearfix fenlei" dd_name="详情所属分类" id="detail-category-path">.*</li>',
                        #     html).group(
                        #     0).split('</span><span class="lie">')
                        # cat_links = list()
                        # for part in cat_part:
                        #     cat_links.append(re.search(r'<a target.*</a>', part).group(0).split('&gt;'))
                        #
                        # cat_href_list = list()
                        # cat_text_list = list()
                        # for links in cat_links:
                        #     for link in links:
                        #         cat_href_list.append(link[link.index('http://'):link.index('.html') + 5])
                        #         cat_text_list.append(link[link.index('>') + 1:link.index('</a>')])
                        #
                        #     cat_href_list.append(';')
                        #     cat_text_list.append(';')
                        #
                        # # 拼接分类文本
                        # cat_text = ''
                        # for s in cat_text_list:
                        #     cat_text += s + '>'
                        # cat_text = cat_text.replace('>;>', ';')
                        # cat_href = ''
                        # for u in cat_href_list:
                        #     cat_href += u + '>'
                        # cat_href = cat_href.replace('>;>', ';')
                        #
                        # # 数据入库
                        # printing_date = ''
                        # for item in data['product_desc_sorted']:
                        #     if item['name'] == '出版信息':
                        #         x = item['content']
                        #         for y in x:
                        #             if y['name'] == '出版时间':
                        #                 printing_date = y['content']
                        #
                        # # 如果必填字段为空 isQualified 字段为0
                        # is_qualified = bool(data['product_info_new']['category_info']['book_detail_category']) \
                        #                and bool(data['product_info_new']['product_name']) \
                        #                and bool(cat_text) \
                        #                and bool(data['product_info_new']['publish_info']['author_name']) \
                        #                and bool(data['product_info_new']['publish_info']['publisher']) \
                        #                and bool(data['product_info_new']['publish_info']['publish_date']) \
                        #                and bool(data['product_info_new']['original_price']) \
                        #                and bool(img_path) \
                        #                and bool(data['product_info_new']['publish_info']['print_copy']) \
                        #                and bool(printing_date) \
                        #                and bool(data['product_info_new']['publish_info']['version_num']) \
                        #                and bool(data['product_info_new']['publish_info']['standard_id']) \
                        #                and bool(data['product_desc']['content']) \
                        #                and bool(data_2['goodRatio']) \
                        #                and bool(also_view)

                        # 插入图书数据
                        data_dic = {
                            "sourceId": source_id,
                            # "bookName": data['product_info_new']['product_name'],
                            # "subName": data['product_info_new']['subname'],
                            # "author": data['product_info_new']['publish_info']['author_name'],
                            # "press": data['product_info_new']['publish_info']['publisher'],
                            # "pubDate": data['product_info_new']['publish_info']['publish_date'],
                            # "price": data['product_info_new']['original_price'],
                            # "isbn": data['product_info_new']['publish_info']['standard_id'],
                            # "edition": data['product_info_new']['publish_info']['version_num'],
                            # "printingDate": printing_date,
                            # "printingNum": data['product_info_new']['publish_info']['print_copy'],
                            # "pageNum": data['product_info_new']['publish_info']['number_of_pages'],
                            # "wordNum": data['product_info_new']['publish_info']['number_of_words'],
                            # "pageSize": data['product_info_new']['publish_info']['product_size'],
                            # "usedPaper": data['product_info_new']['publish_info']['paper_quality'],
                            # "binding": data['product_info_new']['publish_info']['binding'],
                            # "category": data['product_info_new']['category_info']['book_detail_category'],
                            # "catNames": cat_text,
                            # "imgPath": {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                            # "relationProduct": relation_product,
                            # "alsoView": also_view,
                            # "alsoBuy": also_buy,
                            # "goodRatePercent": data_2['goodRatio'],
                            # "goodRateCount": data_2['count'],
                            "updateTime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                            # "editorComment": data['product_desc']['abstract'],
                            # "contentIntroduction": data['product_desc']['content'],
                            # "authorIntroduction": data['product_desc']['authorintro'],
                            # "directory": data['product_desc']['catalog'],
                            # "isQualified": int(is_qualified),
                            "stock": stock,
                            'flag': 1}
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
