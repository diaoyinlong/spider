from conf.py_global import *

def write(file, data):
    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    local_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    file_path = os.path.join(LOG_FOLDER, local_date + '_' + PROJECT_NAME + '_' + str(os.getpid()) + '_' + file)
    ip = getIp()
    if len(ip) > 0:
        write_file(file_path, local_time + '\t[' + ip + ']' + data + '\n')
        print(local_time + '\t[' + ip + ']' + data + '\n')
    else:
        write_file(file_path, local_time + '\t' + data + '\n')
        print(local_time + '\t' + data + '\n')


def log_error(data):
    write('error.log', data)


def log_process(data):
    write('process.log', data)


def log_gather(data):
    write('gather.log', data)
    
def log_write(data):
    if PART == 'Gather':
        write('gather.log', data)
    elif PART == 'Process':
        write('process.log', data)



