from conf.py_global import *


def anti_shield():
    '''
    避免防采集策略：
    '''
    try:
        while REDIS_OBJ.exists(REDIS_KEY_ROUTER_RESTART) > 0:  # 判断是否正在重启路由
            log_write('Wait the router restart...')
            time.sleep(1)

        ip = getIp()
        if ip == '0.0.0.0':
            restart_router()

        key = PART + '_' + ip
        access_num = REDIS_OBJ.get(key)
        if access_num is None:
            REDIS_OBJ.set(key, 0)
        else:
            access_num = int(access_num)
            if PART == 'Gather':
                if access_num >= GATHER_NUM:
                    log_gather('Anti shield start up. Gather will sleep ' + str(GATHER_TIME) + ' seconds!!!')
                    time.sleep(GATHER_TIME)
                    REDIS_OBJ.set(key, 0)

            if PART == 'Process':
                if access_num >= PROCESS_NUM:
                    log_process('Anti shield start up. Process will sleep ' + str(PROCESS_TIME) + ' seconds!!!')
                    time.sleep(PROCESS_TIME)
                    REDIS_OBJ.set(key, 0)
        REDIS_OBJ.incr(key)

        # 定量重启路由
        if IS_RESTART_ROUTER:
            router_num = REDIS_OBJ.get(ip)
            if router_num is None:
                REDIS_OBJ.setex(ip, 0, 3600)
            else:
                router_num = int(router_num)
                if router_num >= ROUTER_NUM:
                    REDIS_OBJ.set(ip, 0)
                    log_write('Restart router...')
                    restart_router()
                    REDIS_OBJ.delete(REDIS_KEY_ANTI + str(os.getpid()))
            REDIS_OBJ.incr(ip)
    except Exception as e:
        log_error("Exception:" + '\t' + str(e))
        traceback.print_exc()
