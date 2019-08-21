import hashlib
import requests
import yaml
import os
import platform
import zipfile
import json
import datetime
from threading import Thread,local,current_thread


def run():

    #获取当前关联的baseUrl等
    baseUrl = local_Upload.baseUrl
    username = local_Upload.username
    password = local_Upload.password
    path = local_Upload.path

    ########################################
    # 请求baseUrl 环境login接口，获取session
    ########################################

    print("开始,进程名为：%s"%current_thread().name)
    t_url = baseUrl + "/user/login/"
    params = {'username': username,
              'password': password
            }
    print(t_url)
    print(params)
    print("：-------------")
    response = requests.post(t_url, data=params)
    print("fanhui，进程名为：%s" % current_thread().name)
    print(response.text)
    print("-----------：")
    cookies = requests.utils.dict_from_cookiejar(response.cookies)  # 返回值 jessionid
    result = response.json()  # 返回值 json
    role = result["data"]["role"]
    user_id = (result["data"]["user_id"])
    # 处理cookies格式
    key = cookies["SESSION"]
    cookies = "SESSION" + "=" + key
    print("登录成功.........")
    print("-----------")


    # ######################################
    # # 解压path文件
    # # 修改 USER.txt 的UUID，uploaderID
    # # 并和 BM.txt重新压缩成之前的path
    # ######################################
    # 获取当前时间，并作为task_id
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    task_id = now
    print("----------------------------------------")
    print("开始读取文件,进程名为：%s" %current_thread().name)
    print(path)
    print("----------------------------------------")
    # 默认模式r，读
    # mutex.acquire()  # 取得锁
    zipRead = zipfile.ZipFile(path)
    # # 返回所有文件夹和文件
    # print(zipRead.namelist())
    # # 返回该zip的文件名
    # print(zipRead.path)

    # 解压压缩包
    zipRead.extractall(os.path.dirname(path))

    # 替换其中的uuid以及uploaderId
    print("替换UUID，以及UploaderId....")
    usertxtPath = os.path.dirname(path) + '/USER.TXT'
    bmtxtPath = os.path.dirname(path) + '/BM.TXT'
    if 'Windows' in platform.system():
        # windows os
        usertxtPath = usertxtPath.replace('/', '\\')
        bmtxtPath = bmtxtPath.replace('/', '\\')
    print("usertxtPath:%s"%usertxtPath)
    print("bmtxtPath:%s"%bmtxtPath)

    with open(usertxtPath, 'r+', encoding="utf-8") as file:
        a = file.read()
        # ######################################
        # 去掉BOM元素
        if a.startswith(u'\ufeff'):
            a = a.encode('utf8')[3:].decode('utf8')
        # ######################################
        rr = json.loads(a)
        print("----------------------------------------")
        print("开始读取原始文件,进程名为：%s" % current_thread().name)
        print(path)
        print(rr)
        print("----------------------------------------")
        rr["uuid"] = now
        rr["uploaderId"] = user_id
        newfile = json.dumps(rr, ensure_ascii=False)
        print("----------------------------------------")
        print("开始读取写入文件,进程名为：%s" % current_thread().name)
        print(path)
        print(newfile)
        print("----------------------------------------")
        file.seek(0)
        file.flush()
        file.write(newfile)
        zipRead.close()
        print("替换完成..........")
    # 获取BM.TXT以及USER.TXT的路径并一起压缩到一起
    # filedir = os.path.dirname(__file__)
    # usertxtPath = filedir + '/USER.TXT'
    # bmtxtPath = filedir + '/BM.TXT'

    print("----------------------------------------")
    print("开始写文件,进程名为：%s" % current_thread().name)
    print(path)
    print("----------------------------------------")
    zipWrite = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
    # for i in [usertxtPath, bmtxtPath]:
    #     file = i.split('/')[-1]
    zipWrite.write(usertxtPath,"USER.TXT")
    zipWrite.write(bmtxtPath,"BM.TXT") # 这个file是文件名，意思是直接把文件添加到zip没有文件夹层级， zipWrite.write(i)这种写法，则会出现上面路径的层级
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
    print("----------------------------------------")
    print("开始上传文件,进程名为：%s" % current_thread().name)
    print(path)
    print("----------------------------------------")
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
                print(res)
            i = i + 1
    print("上传完成..........")
    file.close()  # 关闭文件

    # #####################################
    # # 请求merge接口，分段传入数据合并传入
    # # 的数据
    # #####################################

    print("上传中..........")
    print("----------------------------------------")
    print("开始merge文件,进程名为：%s" % current_thread().name)
    print(path)
    print("----------------------------------------")

    with open(path, "rb") as md5file:
        md5 = hashlib.md5(md5file.read()).hexdigest()
    md5file.close()
    # # print(md5)
    # mutex.release()  # 释放锁
    url = baseUrl + "/upload/merge?task_id=" + task_id + "&md5=" + md5 + "&filename=" + path.split('/')[-1] + ""
    res = requests.get(url, headers=t_headers)
    print(res.text)
    #
    #

if __name__=="__main__":

    ####################################
    # 初始化userList,fileList,pathList
    ####################################
    userList = []
    pathList = []
    fileList = []
    ####################################
    # 获取baseUrl
    ####################################
    path = os.path.dirname(os.path.abspath(__file__)) + "/configfast.yml"
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
    usernames = result["username"]
    password = result["password"]
    files = result["files"]

    #创建全局ThreadLocal对象

    local_Upload = local()


    # 获取到密码后，加密传输给登录
    def sha256(s):
        x = hashlib.sha256()
        x.update(s.encode("utf-8"))
        return x.hexdigest()


    def md5value(s):
        md5 = hashlib.md5()
        md5.update(s)
        return md5.hexdigest()


    def Mkdir(path):
        # 判断路径是否存在
        # 存在     True
        # 不存在   False
        isExists = os.path.exists(path)

        # 判断结果
        if not isExists:
            # 如果不存在则创建目录
            # 创建目录操作函数
            os.mkdir(path)
            print(path + ' 创建成功')

        else:
            # 如果目录存在则不创建，并提示目录已存在
            print(path + ' 目录已存在')

        return path


    def filesplit(files):

        file = files.split(".")[0]
        path = os.path.dirname(os.path.abspath(__file__)) + "/" + file
        if 'Windows' in platform.system():
            # windows os
            path = path.replace('/', '\\')

        path = Mkdir(path)
        path = path + "/" + files

        return path


    #绑定local_Upload 对象
    def process_Upload(baseUrl,username,password,path):
        local_Upload.baseUrl = baseUrl
        local_Upload.username = username
        local_Upload.password = password
        local_Upload.path = path
        run()


    password = sha256(password)



    # 开启多个线程进行上传,获取userlist长度，以及path长度
    thread_list = []
    # mutex = Lock() # 创建锁
    for username in usernames:
        userList.append(username)

    for file in files:
        fileList.append(file)

    j = 0
    if len(userList)>len(fileList):
        print("输入非法，用户数不能比文件数多")
    else:
        for file in fileList:
            path = filesplit(file)
            pathList.append(path)

        for i in range(0,len(pathList)):
            if i <=len(userList)-1:
                j=i
            else:
                j=len(userList)-1

            # print(str(j)+":"+str(i))
            thread = Thread(target=process_Upload, args=(baseUrl, userList[j], password, pathList[i]),name='Thread' + str(i))
            # 启动线程01
            thread_list.append(thread)

        for thread in thread_list:
            thread.setDaemon(True)
            thread.start()

        for thread in thread_list:
            thread.join()

