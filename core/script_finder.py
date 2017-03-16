from conf.py_global import *

class ScriptFinder(HTMLParser):
    '''
    获取html中script标签内的数据
    '''
    def __init__(self):
        super().__init__()
        self.flag = 0
        self.script = ''

    # When we call HTMLParser feed() this function is called when it encounters an opening tag <a>
    def handle_starttag(self, tag, attrs):
        '''
        重写HTMLParser里的方法，当调用feed()时执行，当遇到script标签时将flag置为１
        :param tag:
        :param attrs:
        :return:
        '''
        if tag == 'script':
            for (attribute, value) in attrs:
                if value == 'text/javascript':
                    self.flag = 1

    def handle_data(self, data):
        '''
        重写HTMLParser里的方法,用来获取标签内的数据
        :param data:
        :return:
        '''
        if self.flag == 1:
            self.script = data
            self.flag = 0

    def page_script(self):
        return self.script.lstrip()

    def error(self, message):
        pass
