import sys
sys.path.append("..")
from conf.py_global import *

print(CURL.get_version())

# print(CURL.get("https://api.douban.com/v2/book/isbn/9787807681472"))

# print(CURL.post("http://booklib.kfz.com/gather/interface/addToDB/", 
#                 {"key":"80f0b510fcf7c07cd5c1e4a21eae8242", 
#                  "isbn":"9780060675111",
#                  "bookName":"测试",
#                  "certifyStatus":"failed"}))

# print(CURL.post("http://booklib.kfz.com/gather/interface/addToDB/", 
#                 {"key":"80f0b510fcf7c07cd5c1e4a21eae8242", 
#                  "isbn":"9780060675111", 
#                  "bookName":"测试",
#                  "certifyStatus":"failed",
#                  "smallImg":{"type":"file", "file":"D:/tmp/1c40be7270380b2ae09ffd2ed1e54447_l.jpg"}}))


# print(CURL.post("http://booklib.kfz.com/gatherv2/interface/insertToDangdangDBForSourceBookInfo/", 
#                 {"key":"80f0b510fcf7c07cd5c1e4a21eae8242", 
#                  "isbn":"9780060675111", 
#                  "bookName":"测试",
#                  "certifyStatus":"failed",
#                  "smallImg":{"type":"multiplefile", "file":"D:/tmp/1c40be7270380b2ae09ffd2ed1e54447_l.jpg;D:/tmp/1c40be7270380b2ae09ffd2ed1e54447_m.jpg;",
#                              "target":"dangdang/1c40/1c40be7270380b2ae09ffd2ed1e54447_l.jpg;dangdang/1c40/1c40be7270380b2ae09ffd2ed1e54447_m.jpg"}}))
# 
# 
# print(CURL.post("http://booklib.kfz.com/gatherv2/interface/insertToDangdangDBForSourceBookInfo/", 
#                 {"key":"80f0b510fcf7c07cd5c1e4a21eae8242", 
#                  "isbn":"9780060675111", 
#                  "bookName":"测试",
#                  "certifyStatus":"failed",
#                  "smallImg":{"type":"file", "file":"D:/tmp/1c40be7270380b2ae09ffd2ed1e54447_m.jpg"}}))

# print(CURL.get("http://diviner.jd.com/diviner?lid=1&lim=23&ec=utf-8&p=202000&sku=11971763&callback=jQuery4524797&_=1477639599120",
#                agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36",
#                referer="http://item.jd.com/11971763.html",
#                cookie="__jda=; __jdb=; __jdc=; __jdu="))


# print(CURL.getRandAgent())
# 
# 
# print(CURL.get("http://book.kongfz.com/7694/3794504281111111111111111111/", proxy = "http://110.72.17.71:8123", timeout = 60))


# print(CURL.get("http://192.168.1.1/userRpm/StatusRpm.htm?Disconnect=%B6%CF%20%CF%DF&wan=3", referer="http://192.168.1.1/userRpm/StatusRpm.htm", authorization="Basic YWRtaW46ZjZlNmI2ZGYyZA=="))


# result =os.system('ping 114.114.114.114')
# print(result)
# if result:
#     print('ping fail')
# else:
#     print('ping ok')
#     
# 
# 
# fnull = open(os.devnull, 'w')
# return1 = subprocess.call('ping 192.168.1.149', shell = True, stdout = fnull, stderr = fnull)
# print(return1)
# if return1:
#     print('ping fail')
# else:
#     print('ping ok')
# fnull.close()
# 
# print("exit")




# rUrl = "http://192.168.1.1/"
# authorization = "Basic YWRtaW46ZjZlNmI2ZGYyZA=="
# statusCode = CURL.get(rUrl, authorization=authorization, returnType=1)
# print(statusCode)
# if statusCode == 200:
#     print("ok")
# else:
#     print("no")


# print(CURL.get("https://book.douban.com/tag/英国"))


# url = "https://book.douban.com/tag/英国"
# print(urllib.parse.quote(url, safe=string.printable))
# url = "https://www.amazon.cn/gp/product/B001T9N51M/ref=dp_cgs_a_2_extern?smid=A3TEGLC21NOO5Y"
# print(urllib.parse.quote(url, safe=string.printable))


# x = CURL.get('https://www.baidu.com/',returnType=2)
# print(x)
# exit()

loginHeader = CURL.post('http://192.168.168.1/login.cgi', 
              "username=admin&password=f6e6b6df2d&selectLanguage=CH&LANGUAGE=&OKBTN=%E7%99%BB%E5%BD%95",
              postType = 2,
              agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
              referer="http://192.168.168.1/"
              ,returnType=2
#             ,proxy = "http://192.168.168.168:6666"
            ,cookie="username=%%"
            ,http_header = [
                'Content-Type: application/x-www-form-urlencoded',
                'Pragma: no-cache',
                'Accept-Encoding: gzip, deflate',
                'Accept-Language: zh-CN',
                'Accept: text/html, application/xhtml+xml, */*',
                "Expect:"
                ]
              )
print(loginHeader)
loginHeader = loginHeader.decode('utf-8', 'replace')
hash_key = re.search('hash_key=(\w+),', loginHeader).group(1)
session_id = re.search('session_id=(\w+);', loginHeader).group(1)
print(hash_key)
print(session_id)


interface_status = CURL.get('http://192.168.168.1/interface_status.cgi', 
              agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
              ,returnType=2
            ,proxy = "http://192.168.168.168:6666"
            ,cookie="username=%%; hash_key="+hash_key+",session_id="+session_id
              )
print(interface_status)
interface_status = interface_status.decode('utf-8', 'replace')
hash_key = re.search('hash_key=(\w+),', interface_status).group(1)
session_id = re.search('session_id=(\w+);', interface_status).group(1)
print(hash_key)
print(session_id)


#断开wan2
dankai2 = CURL.post('http://192.168.168.1/interface_status.cgi', 
              "LANGUAGE=&PWAN2D_OKBTN=%E6%96%AD%E5%BC%80WAN2",
              postType = 2,
              agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
              referer="http://192.168.168.1/"
              ,returnType=2
#             ,proxy = "http://192.168.168.168:6666"
            ,cookie="username=%%; hash_key="+hash_key+",session_id="+session_id
            ,http_header = [
                'Content-Type: application/x-www-form-urlencoded',
                'Pragma: no-cache',
                'Accept-Encoding: gzip, deflate',
                'Accept-Language: zh-CN',
                'Accept: text/html, application/xhtml+xml, */*',
                "Expect:"
                ]
              )
print("断开wan2")
print(dankai2)
dankai2 = dankai2.decode('utf-8', 'replace')
hash_key = re.search('hash_key=(\w+),', dankai2).group(1)
session_id = re.search('session_id=(\w+);', dankai2).group(1)
print(hash_key)
print(session_id)

#刷新
shuaxin = CURL.post('http://192.168.168.1/interface_status.cgi', 
              "LANGUAGE=&OKBTN1=%E5%88%B7%E6%96%B0",
              postType = 2,
              agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
              referer="http://192.168.168.1/"
              ,returnType=2
#             ,proxy = "http://192.168.168.168:6666"
            ,cookie="username=%%; hash_key="+hash_key+",session_id="+session_id
            ,http_header = [
                'Content-Type: application/x-www-form-urlencoded',
                'Pragma: no-cache',
                'Accept-Encoding: gzip, deflate',
                'Accept-Language: zh-CN',
                'Accept: text/html, application/xhtml+xml, */*',
                "Expect:"
                ]
              )
print("刷新")
print(shuaxin)
shuaxin = shuaxin.decode('utf-8', 'replace')
hash_key = re.search('hash_key=(\w+),', shuaxin).group(1)
session_id = re.search('session_id=(\w+);', shuaxin).group(1)
print(hash_key)
print(session_id)

#连接wan2
lianjie2 = CURL.post('http://192.168.168.1/interface_status.cgi', 
              "LANGUAGE=&PWAN2L_OKBTN=%E8%BF%9E%E6%8E%A5WAN2",
              postType = 2,
              agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
              referer="http://192.168.168.1/"
              ,returnType=2
#             ,proxy = "http://192.168.168.168:6666"
            ,cookie="username=%%; hash_key="+hash_key+",session_id="+session_id
            ,http_header = [
                'Content-Type: application/x-www-form-urlencoded',
                'Pragma: no-cache',
                'Accept-Encoding: gzip, deflate',
                'Accept-Language: zh-CN',
                'Accept: text/html, application/xhtml+xml, */*',
                "Expect:"
                ]
              )
print("连接wan2")
print(lianjie2)
lianjie2 = lianjie2.decode('utf-8', 'replace')
hash_key = re.search('hash_key=(\w+),', lianjie2).group(1)
session_id = re.search('session_id=(\w+);', lianjie2).group(1)
print(hash_key)
print(session_id)






