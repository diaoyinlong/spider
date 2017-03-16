from conf.py_global import *


class CommonModel:
    '''
          通用数据操作类
    '''

    def __init__(self):
        self.errInfo = ''

    def getErr(self):
        return self.errInfo

    def setErr(self, msg):
        self.errInfo = msg

    def formatResponse(self, response):
        '''
                    格式化请求返回
        '''
        if len(response) < 10:
            self.setErr("the response is invalid.")
            return False
        result = response.decode()
        resultDict = json.loads(result)
        if 'status' not in resultDict:
            self.setErr("the response is invalid. => " + result)
            return False
        if resultDict['message'] == None:
            resultDict['message'] = ''
        if resultDict['status'] != True:
            self.setErr(resultDict['message'])
            return False
        return resultDict['data']
