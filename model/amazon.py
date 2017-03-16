from conf.py_global import *


class amazon(CommonModel):
    '''
          亚马逊数据操作类
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
        response = CURL.post(SITES['amazon_get_book_num_by_sourceid'], data, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(sourceId) + " => amazon_get_book_num_by_sourceid : " + self.getErr())
            return -1
        return int(result['num'])

    def insert_bookinfo(self, bookinfo):
        '''
        数据入库及图片上传
        '''
        bookinfo['___key'] = SITES['key']
        response = CURL.post(SITES['amazon_insert_bookinfo'], bookinfo, agent='kfz-agent')
        result = self.formatResponse(response)
        if result == False:
            self.setErr("sourceid : " + str(bookinfo['sourceId']) + " => amazon_insert_bookinfo : " + self.getErr())
            return -1
        return int(result['bookId'])

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

                    html = CURL.get(uri, referer='https://www.amazon.cn/').decode()

                    # 判断是否有货
                    if 'dynamicDeliveryMessage' in html and '目前无货' in html:
                        stock = 0
                    else:
                        stock = 1

                    # 开始正则匹配图书基本信息
                    base_info = re.search(r'<div id="detail_bullets_id">(.*?)</div>', html, re.S).group(1)

                    # 对电子书不做处理
                    if re.search(r'<li><b>版本：</b> Kindle电子书</li>', base_info):
                        log_process('Do not process Kindle e book continue...')
                        continue

                    source_id = re.search(r'<li><b>ASIN: </b>(.*)</li>', base_info).group(1).strip()

                    # 判断source_id是否存在
                    exist_id = self.get_booknum_with_source_id(source_id)
                    if exist_id < 0:
                        log_error(self.getErr())
                        continue
                    elif exist_id > 0:
                        log_process("sourceid : " + source_id + " => has exists in db.")
                        uri_md5 = hashlib.md5(uri.encode('utf-8')).hexdigest()
                        IS_CHECK_PROD and REDIS_OBJ.set(REDIS_KEY_CHECK_PROD + uri_md5, '')
                        continue

                    base_info_i_1 = CURL.get('https://www.amazon.cn/gp/aw/d/' + source_id + '/ref=mw_dp_mpd?pd=1',
                                             referer='https://www.amazon.cn/').decode()

                    base_info_i_2 = CURL.get('https://www.amazon.cn/gp/aw/d/' + source_id,
                                             referer='https://www.amazon.cn/').decode()

                    # 解析出版社
                    result = re.search(r'发行人:(.*)<br />', base_info_i_1)
                    if result is None:
                        press = ''
                    else:
                        result = result.group(1).strip()
                        index = result.index(';')
                        press = result[index + 1:]

                    # 解析发布日期
                    result = re.search(r'发布日期:(.*)<br />', base_info_i_1).group(1).strip()
                    index = result.index(';')
                    pub_date = result[index + 1:]

                    # 解析标题
                    title = re.search(r'<h1 id="title" class="a-size-large a-spacing-none">.*</h1>', html, re.S)
                    if title is None:
                        book_name = ''
                    else:
                        title = title.group()

                        # 解析书名
                        result = re.search(r'<span id="productTitle" class="a-size-large">(.*)</span>', title)
                        if result is None:
                            book_name = ''
                        else:
                            book_name = result.group(1).strip()
                        book_name = parser.unescape(book_name)

                    # 解析外文书名
                    result = re.search(r'<li><b>外文书名:</b>.*<a .*>(.*)</a></li>', base_info)
                    if result is None:
                        foreign_name = ''
                    else:
                        foreign_name = result.group(1).strip()

                    # 解析语种
                    result = re.search(r'<li><b>语种：</b>(.*)</li>', base_info)
                    if result is None:
                        language = ''
                    else:
                        language = result.group(1).strip()

                    # 解析作者
                    result = re.search(
                        r'<div id="byline" class="a-section a-spacing-micro bylineHidden feature">(.*?)<div id="qpeTitleTag_feature_div" class="feature" data-feature-name="qpeTitleTag">',
                        html, re.S)
                    if result is None:
                        author = ''
                    else:
                        result = result.group(1).strip()
                        author_arr = result.split('<span class="author notFaded" data-width="">')
                        author = ''
                        for item in author_arr:
                            if item == '':
                                continue
                            else:
                                item = item.strip()
                                n1 = re.search(r'<a.*class="a-link-normal contributorNameID".*>(.*)</a>', item)
                                if n1 is None:
                                    n1 = re.search(r'<a class="a-link-normal".*>(.*)</a>', item)

                                n1 = n1.group(1)
                                n2 = re.search(r'<span class="a-color-secondary">(.*)</span>', item).group(1)
                                author += n1 + n2

                    # 解析定价
                    result = re.search(r'<span class="dpListPrice">(.*)</span>', base_info_i_2)
                    if result is None:
                        price = ''
                    else:
                        price = result.group(1).lstrip('￥')

                    # 解析ISBN
                    result = re.search(r'<li><b>ISBN:</b>(.*)</li>', base_info)
                    if result is None:
                        isbn = ''
                    else:
                        isbn_arr = result.group(1).split(',')
                        isbn = ''
                        for item in isbn_arr:
                            item = item.strip()
                            if len(item) == 13 and (item[:3] == '978' or item[:3] == '979'):
                                isbn = item

                    # 解析条形码
                    result = re.search(r'<li><b>条形码:</b>(.*)</li>', base_info)
                    if result is None:
                        bar_code = ''
                    else:
                        bar_code = result.group(1).strip()

                    # 解析版次
                    result = re.search(r'<li><b>出版社:</b>.*第(\d*)版.*</li>', base_info)
                    if result is None:
                        edition = ''
                    else:
                        edition = result.group(1).strip()

                    # 解析页数
                    result = re.search(r'页数:&nbsp;(.*)<br />', base_info_i_1)
                    if result is None:
                        page_num = ''
                    else:
                        page_num = result.group(1).strip().replace(' ', '')

                    # 解析装订
                    result = re.search(r'<li><b>(.*)</b> ' + page_num + '</li>', base_info)
                    if result is None:
                        binding = ''
                    else:
                        binding = result.group(1).rstrip(':')

                    # 解析开本
                    result = re.search(r'<li><b>开本:</b>(.*)</li>', base_info)
                    if result is None:
                        page_size = ''
                    else:
                        page_size = result.group(1).strip()

                    # 解析商品尺寸
                    result = re.search(r'<li><b>\s.*商品尺寸: \s.*</b>\s(.*)', base_info)
                    if result is None:
                        prod_size = ''
                    else:
                        prod_size = result.group(1).strip()

                    # 解析商品重量
                    result = re.search(r'<li><b>\s.*商品重量: \s.*</b>\s(.*)', base_info)
                    if result is None:
                        prod_weight = ''
                    else:
                        prod_weight = result.group(1).strip()

                    # 解析品牌
                    result = re.search(r'<li><b>品牌:</b>(.*)</li>', base_info)
                    if result is None:
                        brand = ''
                    else:
                        brand = result.group(1).strip()

                    # 解析当前分类
                    result = re.search(r'<ul class="a-unordered-list a-horizontal a-size-small">(.*?)</ul>', html, re.S)
                    if result is None:
                        cat_name = ''
                    else:
                        temp = result.group(1)
                        cat_name = ''
                        cat_arr = temp.split('</span>')
                        for item in cat_arr:
                            result = re.search(r'<a class="a-link-normal a-color-tertiary".*>(.*)</a>', item, re.S)
                            if result is None:
                                continue
                            cat_name += result.group(1).strip() + '>'
                    cat_name = cat_name.rstrip('>')

                    # 解析所有分类
                    result = re.search(r'<ul class="zg_hrsr">(.*?)</ul>', html, re.S)
                    if result is None:
                        cat_names = ''
                    else:
                        cat_names = ''
                        temp_arr = result.group(1).strip().split('</li>')
                        for temp in temp_arr:
                            if temp == '':
                                continue
                            name_arr = temp.split(' &gt; ')
                            for name in name_arr:
                                name = re.search(r'<a href=.*>(.*)</a>', name).group(1)
                                cat_names += name + '>'
                            cat_names = cat_names.rstrip('>') + ';'

                    # 解析图片路径并存储图片（目录名称为source_id后3位）
                    result = re.search(r'<span class=.* id="imgThumbs">(.*?)</span>', html, re.S)
                    if result is None:
                        img_path = ''
                        img_path___Target = ''
                    else:
                        result = result.group(1).strip()
                        img_arr = result.split('</div>')
                        img_path = ''
                        img_path___Target = ''
                        for raw_img in img_arr:
                            raw_img = re.search(r'<img src="(.*)">', raw_img)
                            if raw_img is None:
                                continue
                            else:
                                raw_img = raw_img.group(1)
                                s = raw_img.split('/')
                                raw_img_name = s[len(s) - 1]
                                n = raw_img_name.split('.')
                                img_name = n[0] + '.' + n[len(n) - 1]
                                if img_path___Target.find(img_name) >= 0:
                                    continue
                                new_img = raw_img[:raw_img.rindex('/') + 1] + img_name
                                img_path += os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[-3:], img_name) + ';'
                                img_path___Target += os.path.join(PROJECT_NAME, source_id[-3:], img_name) + ';'
                                create_project_dir(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[-3:]))
                                save_remote_img(os.path.join(DATA_FOLDER, PROJECT_NAME, source_id[-3:], img_name),
                                                new_img)
                        log_process("sourceid : " + source_id + ' => Call the remote interface to store data...')

                    # 解析丛书名
                    result = re.search(r'<li><b>丛书名:</b>&nbsp;<a.*>(.*)</a></li>', base_info)
                    if result is None:
                        series = ''
                    else:
                        series = result.group(1)

                    # 解析买了还买
                    result = re.search(r'<ol class="a-carousel" role="list">(.*?)</ol>', html, re.S)
                    if result is None:
                        buy_after_buy = ''
                    else:
                        buy_after_buy = ''
                        result = result.group(1).strip()
                        s_arr = result.split('</li>')
                        for s in s_arr:
                            if s == '':
                                continue
                            s = re.search(r'<div data-p13n-asin-metadata="\{.*&quot;asin&quot;:&quot;(.*)&quot;}.*">',
                                          s).group(1)
                            buy_after_buy += s + ';'

                    # 解析看过还买
                    result = re.search(r'<ul class="a-nostyle a-vertical p13n-sc-list-cells">(.*?)</ul>', html, re.S)
                    if result is None:
                        view_after_buy = ''
                    else:
                        view_after_buy = ''
                        result = result.group(1).strip()
                        s_arr = result.split('</li>')
                        for s in s_arr:
                            if s == '':
                                continue
                            s = re.search(r'<div data-p13n-asin-metadata="\{.*&quot;asin&quot;:&quot;(.*)&quot;}.*">',
                                          s).group(1)
                            view_after_buy += s + ';'

                    # 平均星级
                    result = re.search(r'<div id="summaryStars" class="a-row">(.*?)</div>', html, re.S)
                    if result is None:
                        avg_rate = ''
                        rate_num = ''
                    else:
                        result = result.group(1).strip()
                        avg_rate = re.search(r'<span class="a-icon-alt">平均(.*)星</span>', result).group(1).strip()
                        rate_num = re.search(r'</i>\s(.*)\s.*</a>', result).group(1).strip()

                    # 编辑推荐
                    result = re.search(r'<b>&#32534;&#36753;&#25512;&#33616;</b><br />(.*?)<br />', base_info_i_1)

                    if result is None:
                        result2 = re.search(r'<b>编辑推荐</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            editor_comment = ''
                        else:
                            editor_comment = result2.group(1).strip()
                    else:
                        editor_comment = result.group(1).strip()

                    # 名人推荐
                    result = re.search(r'<b>&#21517;&#20154;&#25512;&#33616;</b><br />(.*?)<br />', base_info_i_1)
                    if result is None:
                        result2 = re.search(r'<b>名人推荐</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            famous_comment = ''
                        else:
                            famous_comment = result2.group(1).strip()
                    else:
                        famous_comment = result.group(1).strip()

                    # 媒体推荐
                    result = re.search(r'<b>&#23186;&#20307;&#25512;&#33616;</b><br />(.*?)<br />', base_info_i_1)
                    if result is None:
                        result2 = re.search(r'<b>媒体推荐</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            media_comment = ''
                        else:
                            media_comment = result2.group(1).strip()
                    else:
                        media_comment = result.group(1).strip()

                    # 内容简介
                    result = re.search(r'<b>&#20869;&#23481;&#31616;&#20171;</b><br />(.*?)<br />', base_info_i_1)
                    if result is None:
                        result2 = re.search(r'<b>内容简介</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            content_intro = ''
                        else:
                            content_intro = result2.group(1).strip()
                    else:
                        content_intro = result.group(1).strip()

                    # 作者简介
                    result = re.search(r'<b>&#20316;&#32773;&#31616;&#20171;</b><br />(.*?)<br />', base_info_i_1)
                    if result is None:
                        result2 = re.search(r'<b>作者简介</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            author_intro = ''
                        else:
                            author_intro = result2.group(1).strip()
                    else:
                        author_intro = result.group(1).strip()

                    # 目录
                    result = re.search(r'<b>&#30446;&#24405;</b><br />(.*?)<br />', base_info_i_1)
                    if result is None:
                        result2 = re.search(r'<b>目录</b><br />(.*?)<br />', base_info_i_1)
                        if result2 is None:
                            catalog = ''
                        else:
                            catalog = result2.group(1).strip()
                    else:
                        catalog = result.group(1).strip()

                    is_qualified = bool(cat_name) \
                                   and bool(book_name) \
                                   and bool(author) \
                                   and bool(img_path) \
                                   and bool(price) \
                                   and bool(content_intro) \
                                   and bool(buy_after_buy) \
                                   and bool(press) \
                                   and bool(page_size) \
                                   and bool(isbn) \
                                   and bool(bar_code) \
                                   and bool(prod_size) \
                                   and bool(prod_weight) \
                                   and bool(avg_rate) \
                                   and bool(editor_comment) \
                                   and bool(author_intro) \
                                   and bool(view_after_buy)

                    # 入库前的数据字典
                    data_dic = {
                        'sourceId': source_id,
                        'bookName': book_name,
                        'foreignName': foreign_name,
                        'language': language,
                        'author': author,
                        'press': press,
                        'pubDate': pub_date,
                        'price': price,
                        'isbn': isbn,
                        'barCode': bar_code,
                        'edition': edition,
                        'pageNum': page_num,
                        'pageSize': page_size,
                        'prodSize': prod_size,
                        'prodWeight': prod_weight,
                        'binding': binding,
                        'brand': brand,
                        'category': cat_name,
                        'catNames': cat_names,
                        'imgPath': {"type": "multiplefile", "file": img_path, "target": img_path___Target},
                        'series': series,
                        'buyAfterBuy': buy_after_buy,
                        'viewAfterBuy': view_after_buy,
                        'avgRate': avg_rate,
                        'rateNum': rate_num,
                        'editorComment': editor_comment,
                        'famousComment': famous_comment,
                        'mediaComment': media_comment,
                        'contentIntroduction': content_intro,
                        'authorIntroduction': author_intro,
                        'directory': catalog,
                        'crawledTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                        'isQualified': int(is_qualified),
                        'stock': stock,
                        "___cat_text": cat_names
                    }
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
        pass