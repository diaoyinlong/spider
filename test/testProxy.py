import re
import sys
import traceback
sys.path.append("..")
from core.curl import *

baseUrl = "http://www.kuaidaili.com/proxylist/$i/"
crawledProxyList = []
goodProxyList = []
realGoodProxyList = []
for i in range(1, 11):
    try :
        url = baseUrl.replace("$i", str(i))
        html = CURL.get(url).decode('utf-8', 'replace')
        pattern_ip = re.compile(r'<td data-title="IP">(.*)</td>')
        ipList = pattern_ip.findall(html)
        pattern_port = re.compile(r'<td data-title="PORT">(.*)</td>')
        portList = pattern_port.findall(html)
    except Exception as e:
        traceback.print_exc()
        continue
    
    for ip,port in zip(ipList, portList):
        crawledProxyList.append(ip + ":" + port)
        
    for p in crawledProxyList:
        try :
            CURL.get("http://book.kongfz.com/7694/3794504281111111111111111111/", proxy = "http://" + p)
            goodProxyList.append(p)
        except Exception as e:
            traceback.print_exc()
    print(goodProxyList)

print(goodProxyList)

for pp in goodProxyList:
    try :
        CURL.get("http://book.kongfz.com/7694/3794504281111111111111111111/", proxy = "http://" + p)
        realGoodProxyList.append(pp)
    except Exception as e:
        traceback.print_exc()
    print(realGoodProxyList)

print("exit")
exit()









