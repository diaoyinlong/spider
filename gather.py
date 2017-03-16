from conf.py_global import *

# 当多个进程同时开启时可以继续爬取
entry = ''
if REDIS_OBJ.exists(REDIS_KEY_QUEUED):
    entry = pop_from_redis(REDIS_KEY_QUEUED)
else:
    entry = HOMEPAGE

Spider(PROJECT_NAME, entry)

# instance the lock
mutex = threading.Lock()


# Create worker threads (will die when main exits)
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = False
        t.start()


# Do the next job in the queue
def work():
    while True:
        try:
            if REDIS_OBJ.llen(REDIS_KEY_CRAWLED) > MAX_CRAWLED_QUEUE_LEN:
                log_gather("crawled queue is too long , sleep...")
                time.sleep(3600)
                continue
            url = pop_from_redis(REDIS_KEY_QUEUED)
            if url == '':
                log_gather("queued list is null...")
                time.sleep(10)
                continue

            url_md5 = hashlib.md5(url.encode('utf-8')).hexdigest()

            if (IS_CHECK_CAT and REDIS_OBJ.exists(REDIS_KEY_CHECK_CAT + url_md5)) or (
                        IS_CHECK_PROD and REDIS_OBJ.exists(REDIS_KEY_CHECK_PROD + url_md5)):
                log_gather("category url exist in check queue...")
                continue

            Spider.crawl_page(threading.current_thread().name, url)

            if IS_CHECK_CAT and re.compile(CAT_PATTERN).match(url):
                REDIS_OBJ.setex(REDIS_KEY_CHECK_CAT + hashlib.md5(url.encode('utf-8')).hexdigest(), url, 7 * 24 * 3600)

            if mutex.acquire():
                # 放屏蔽策略
                anti_shield()
                mutex.release()

        except Exception as e:
            log_error(str(e))
            traceback.print_exc()
            time.sleep(3)
            continue


create_workers()
