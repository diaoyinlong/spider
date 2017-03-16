from conf.py_global import *


class Spider:
    '''
    爬虫核心类，用来爬取页面数据
    '''
    project_name = ''
    base_url = ''
    domain_name = ''
    charset = ''
    data_path = ''
    queue = set()
    crawled = set()

    def __init__(self, project_name, base_url):
        Spider.project_name = project_name
        Spider.base_url = base_url
        Spider.data_path = os.path.join(DATA_FOLDER, Spider.project_name)
        Spider.charset = CHARSET
        self.boot()
        self.crawl_page('First spider', Spider.base_url)

    # Creates directory and files for project on first run and starts the spider
    @staticmethod
    def boot():
        '''
        初始化数据存储文件
        :return:
        '''

        create_project_dir(Spider.data_path)

    # Updates user display, fills queue and updates files
    @staticmethod
    def crawl_page(thread_name, page_url):
        '''
        爬取页面　将当前页面内的所有链接缓存到队列并将该页面的链接从队列里删除，记录到已爬取队列
        :param thread_name:
        :param page_url:
        :return:
        '''
        log_gather(thread_name + ' now crawling ' + page_url)
        Spider.add_links_to_set(Spider.gather_links(page_url))
        # Spider.crawled.add(page_url)
        Spider.update_redis()
        log_gather(
            'Queue ' + str(REDIS_OBJ.llen(REDIS_KEY_QUEUED)) + ' | Crawled  ' + str(REDIS_OBJ.llen(REDIS_KEY_CRAWLED)))

    # Converts raw response data into readable information and checks for proper html formatting
    @staticmethod
    def gather_links(page_url):
        try:
            response = CURL.get(page_url)
            html_string = response.decode(CHARSET, 'replace')
            finder = LinkFinder(Spider.base_url, page_url)
            finder.feed(html_string)
        except Exception as e:
            log_error(str(e))
            return set()
        return finder.page_links()

    # Get script content in html
    @staticmethod
    def gather_script(page_url, referer=''):
        try:
            response = CURL.get(page_url, referer=referer)
            html_string = response.decode('utf-8', 'replace')
            finder = ScriptFinder()
            finder.feed(html_string)
        except Exception as e:
            log_error(str(e))
            return set()
        return finder.page_script()

    # Get picture in html
    @staticmethod
    def gather_img(page_url):
        try:
            response = CURL.get(page_url)
            html_string = response.decode('utf-8', 'replace')
            finder = ImgFinder()
            finder.feed(html_string)
        except Exception as e:
            log_error(str(e))
            return set()
        return finder.img_links()

    # Saves queue data to project files
    @staticmethod
    def add_links_to_set(links):
        white_list = re.compile(WHITE_LIST)
        for url in links:
            if (url in Spider.queue) or (url in Spider.crawled):  # 队列去重
                continue

            # 已经处理过的分类和商品不加入队列
            if (IS_CHECK_CAT and re.compile(CAT_PATTERN).match(url) and (
                        REDIS_OBJ.exists(
                                REDIS_KEY_CHECK_CAT + hashlib.md5(url.encode('utf-8')).hexdigest()) is True)) or (
                            IS_CHECK_PROD and re.compile(PROD_PATTERN).match(url) and (
                                REDIS_OBJ.exists(
                                        REDIS_KEY_CHECK_PROD + hashlib.md5(url.encode('utf-8')).hexdigest()) is True)):
                continue

            if white_list.match(url):
                url = parse.quote(url, safe=string.printable)
                url = url.split('#')[0]
                Spider.queue.add(url)
                if re.compile(PROD_PATTERN).match(url):  # 只有商品才进去crawled队列
                    Spider.crawled.add(url)

    @staticmethod
    def update_redis():
        push_all_to_redis(REDIS_KEY_CRAWLED, Spider.crawled)
        push_all_to_redis(REDIS_KEY_QUEUED, Spider.queue)
        Spider.crawled.clear()
        Spider.queue.clear()
