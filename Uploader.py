import hashlib
import requests
import yaml
import os
import platform
import zipfile
import json
import datetime,time
from threading import Thread,Lock
from multiprocessing import Lock,Process

def run(mutex,baseUrl,username,password,path):
    ########################################
    # 请求baseUrl 环境login接口，获取session
    ########################################

    t_url = baseUrl + "/user/login/"
    params = {'username': username,
              'password': password
            }
    print(t_url)
    print(params)
    response = requests.post(t_url, data=params)
    print(response.text)
    cookies = requests.utils.dict_from_cookiejar(response.cookies)  # 返回值 jessionid
    result = response.json()  # 返回值 json
    role = result["data"]["role"]
    user_id = (result["data"]["user_id"])
    # 处理cookies格式
    key = cookies["SESSION"]
    cookies = "SESSION" + "=" + key
    print("登录成功.........")


    # ######################################
    # # 解压path文件
    # # 修改 USER.txt 的UUID，uploaderID
    # # 并和 BM.txt重新压缩成之前的path
    # ######################################
    # 获取当前时间，并作为task_id
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    task_id = now
    print(path)
    print("task_id:%s"%task_id)
    # 默认模式r，读
    mutex.acquire()  # 取得锁
    zipRead = zipfile.ZipFile(path)
    # # 返回所有文件夹和文件
    # print(zipRead.namelist())
    # # 返回该zip的文件名
    # print(zipRead.path)

    # 解压压缩包
    zipRead.extractall()

    # 替换其中的uuid以及uploaderId
    print("替换UUID，以及UploaderId....")
    file = open('USER.TXT', 'r+', encoding="utf-8")
    a = file.read()
    # ######################################
    # 去掉BOM元素
    if a.startswith(u'\ufeff'):
        a = a.encode('utf8')[3:].decode('utf8')
    # ######################################
    rr = json.loads(a)
    print("----------------------------------------")
    print("开始读取原始文件")
    print(path)
    print(rr)
    print("----------------------------------------")
    rr["uuid"] = now
    rr["uploaderId"] = user_id
    newfile = json.dumps(rr, ensure_ascii=False)
    file.seek(0)
    file.flush()
    print("----------------------------------------")
    print("开始读取写入文件")
    print(path)
    print(newfile)
    print("----------------------------------------")
    file.write(newfile)
    file.close()
    zipRead.close()
    print("替换完成..........")
    # 获取BM.TXT以及USER.TXT的路径并一起压缩到一起
    # filedir = os.path.dirname(__file__)
    # usertxtPath = filedir + '/USER.TXT'
    # bmtxtPath = filedir + '/BM.TXT'

    zipWrite = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
    # for i in [usertxtPath, bmtxtPath]:
    #     file = i.split('/')[-1]
    zipWrite.write('USER.TXT')
    zipWrite.write('BM.TXT') # 这个file是文件名，意思是直接把文件添加到zip没有文件夹层级， zipWrite.write(i)这种写法，则会出现上面路径的层级
    zipWrite.close()

    # #####################################
    # # 请求uploader接口，分段传入数据
    # #####################################

    url = baseUrl + "/upload/start"

    # 折中方案，参数按如下方式组织，也是模拟multipart/form-data的核心

    t_headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Mobile Safari/537.36",
        "Cookie": cookies
    }


    def md5value(s):
        md5 = hashlib.md5()
        md5.update(s)
        return md5.hexdigest()

    print("上传中..........")
    with open(path, "rb") as file:
        i = 0
        while True:
            aLine = file.read(1024 * 1024)
            if (len(aLine) == 0):
                break
            else:
                md5 = md5value(aLine)
                params = {"task_id": task_id, "chunk": i, "md5": md5, "filename": path.split('/')[-1]}
                res = requests.post(url, data=params, files={'file': aLine}, headers=t_headers)
            i = i + 1
    print("上传完成..........")
    file.close()  # 关闭文件

    # #####################################
    # # 请求merge接口，分段传入数据合并传入
    # # 的数据
    # #####################################
    with open(path, "rb") as md5file:
        md5 = hashlib.md5(md5file.read()).hexdigest()
    md5file.close()
    # print(md5)
    mutex.release()  # 释放锁
    url = baseUrl + "/upload/merge?task_id=" + task_id + "&md5=" + md5 + "&filename=" + path.split('/')[-1] + ""
    res = requests.get(url, headers=t_headers)
    print(res.text)



if __name__=="__main__":

    ####################################
    # 获取baseUrl
    ####################################
    path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
    if 'Windows' in platform.system():
        # windows os
        path = path.replace('/', '\\')

    try:
        result = yaml.load(open(path, 'r', encoding='utf-8'), Loader=yaml.FullLoader)
    except yaml.YAMLError as err:
        print("YAMLError: ", err)
        result = ""
    print(result)
    baseUrl = result["baseUrl"]
    username = result["username"]
    password = result["password"]
    paths = result["path"]

    # print(len(path))

    # 获取到密码后，加密传输给登录
    def sha256(s):
        x = hashlib.sha256()
        x.update(s.encode("utf-8"))
        return x.hexdigest()


    def md5value(s):
        md5 = hashlib.md5()
        md5.update(s)
        return md5.hexdigest()

    password = sha256(password)
    #判断path是单文件还是多文件，使用不同的方式，多文件需要加锁
    if type(paths)==str:
        #只开启一个线程进行上传
        print("开启一个线程进行上传")
        thread_01 = Thread(target=run,args=(baseUrl,username,password,paths))
        thread_01.start()
    elif type(paths)==list:
        # 开启多个线程进行上传
        thread_list = []
        mutex = Lock() # 创建锁
        for path in paths:
            thread = Thread(target=run,args=(mutex,baseUrl,username,password,path))
            # 启动线程01
            thread_list.append(thread)

        for thread in thread_list:
            thread.setDaemon(True)
            thread.start()
            time.sleep(1)

        for thread in thread_list:
            thread.join()


    else:
        print("请输入str或者list格式")
