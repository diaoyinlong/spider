from conf.py_global import *

class LinkFinder(HTMLParser):
    '''
    获取html中的链接
    '''

    def __init__(self, base_url, page_url):
        super().__init__()
        self.base_url = base_url
        self.page_url = page_url
        self.links = set()

    # When we call HTMLParser feed() this function is called when it encounters an opening tag <a>
    def handle_starttag(self, tag, attrs):
        '''
        重写HTMLParser里的方法，当调用feed()时执行，用来获取页面中的a标签内的href属性值
        :param tag:
        :param attrs:
        :return:
        '''
        if tag == 'a':
            for (attribute, value) in attrs:
                if attribute == 'href':
                    url = parse.urljoin(self.base_url, value)
                    self.links.add(url)

    def page_links(self):
        return self.links

    def error(self, message):
        pass
