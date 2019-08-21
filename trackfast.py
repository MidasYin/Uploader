import hashlib
import requests
import yaml
import os
import platform
import zipfile
import json
import datetime

####################################
#获取baseUrl
####################################
path = os.path.dirname(os.path.abspath(__file__)) + "/configfast.yml"
if 'Windows' in platform.system():
    # windows os
    path = path.replace('/', '\\')

try:
    result = yaml.load(open(path), Loader=yaml.FullLoader)
except yaml.YAMLError as err:
    print("YAMLError: ", err)
    result = ""

# baseUrl = result["baseUrl"]
# username = result["username"]
# password = result["password"]
onlineUrl = result["onlineUrl"]
onlineUsername = result["onlineUsername"]
onlinePassword = result["onlinePassword"]

#获取到密码后，加密传输给登录
def sha256(s):
    x = hashlib.sha256()
    x.update(s.encode("utf-8"))
    return x.hexdigest()


# password = sha256(password)
onlinePassword = sha256(onlinePassword)


#####################################
# 1、请求线上login接口，获取session
# 2、下载报告并命名为repord_id.zip
#####################################
t_url = onlineUrl+"/user/login/"
params = {'username':onlineUsername,
'password' :onlinePassword
}

response = requests.post(t_url,data=params)
cookies = requests.utils.dict_from_cookiejar(response.cookies)  # 返回值 jessionid
result = response.json()  # 返回值 json
# 处理cookies格式
key = cookies["SESSION"]
cookies = "SESSION" + "=" + key



report_ids = input("please input  Online reportIds:")
for report_id in report_ids.split(","):
    url = onlineUrl + "/downloadOriginalFile?"+"report_id="+report_id
    print(url)
    print("下载中......")
    t_headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Mobile Safari/537.36",
        "Cookie": cookies
    }

    Filename = report_id + ".zip"
    response = requests.get(url,headers=t_headers)

    if response.status_code == 200:
        #filename 名为报告名.zip
        path = os.path.dirname(os.path.abspath(__file__)) + "/" + report_id

        if 'Windows' in platform.system():
            # windows os
            path = path.replace('/', '\\')
        print(path)
        isExists = os.path.exists(path)
        if not isExists:
            os.mkdir(path)
        path = path + "/" + Filename

        with open(path, "wb+") as code:
            code.write(response.content)
            print("下载完成")

            # ########################################
            # # 请求baseUrl 环境login接口，获取session
            # ########################################
            # t_url = baseUrl + "/user/login/"
            # params = {'username': username,
            #           'password': password
            #           }
            #
            # response = requests.post(t_url, data=params)
            # cookies = requests.utils.dict_from_cookiejar(response.cookies)  # 返回值 jessionid
            # result = response.json()  # 返回值 json
            # role = result["data"]["role"]
            # user_id = (result["data"]["user_id"])
            # # 处理cookies格式
            # key = cookies["SESSION"]
            # cookies = "SESSION" + "=" + key
            # print(cookies)
            #
            # # ######################################
            # # # 解压Filename文件
            # # # 修改 USER.txt 的UUID，uploaderID
            # # # 并和 BM.txt重新压缩成之前的Filename
            # # ######################################
            # # 获取当前时间，并作为task_id
            # now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            # task_id = now
            #
            # # 默认模式r，读
            # zipRead = zipfile.ZipFile(Filename)
            # # 返回所有文件夹和文件
            # print(zipRead.namelist())
            # # 返回该zip的文件名
            # print(zipRead.filename)
            #
            # # 解压压缩包
            # zipRead.extractall()
            #
            # # 替换其中的uuid以及uploaderId
            # file = open('USER.TXT', 'r+', encoding="utf-8")
            # a = file.read()
            # print(a)
            # rr = json.loads(a)
            # rr["uuid"] = now
            # rr["uploaderId"] = user_id
            # newfile = json.dumps(rr, ensure_ascii=False)
            # print(newfile)
            # file.seek(0)
            # file.flush()
            # file.write(newfile)
            # file.close()
            # zipRead.close()
            #
            # # 获取BM.TXT以及USER.TXT的路径并一起压缩到一起
            # filedir = os.path.dirname(__file__)
            # usertxtPath = filedir + '/USER.TXT'
            # bmtxtPath = filedir + '/BM.TXT'
            #
            # zipWrite = zipfile.ZipFile(Filename, 'w', zipfile.ZIP_DEFLATED)
            # for i in [usertxtPath, bmtxtPath]:
            #     file = i.split('/')[-1]
            #     zipWrite.write(i, file)  # 这个file是文件名，意思是直接把文件添加到zip没有文件夹层级， zipWrite.write(i)这种写法，则会出现上面路径的层级
            # zipWrite.close()
            #
            # # #####################################
            # # # 请求uploader接口，分段传入数据
            # # #####################################
            #
            # url = baseUrl + "/upload/start"
            #
            # # 折中方案，参数按如下方式组织，也是模拟multipart/form-data的核心
            #
            # t_headers = {
            #     "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Mobile Safari/537.36",
            #     "Cookie": cookies
            # }
            #
            #
            # def md5value(s):
            #     md5 = hashlib.md5()
            #     md5.update(s)
            #     return md5.hexdigest()
            #
            #
            # with open(Filename, "rb") as file:
            #     i = 0
            #     while True:
            #         aLine = file.read(1024 * 1024)
            #         if (len(aLine) == 0):
            #             break
            #         else:
            #             md5 = md5value(aLine)
            #             print(md5)
            #             print(aLine)
            #             params = {"task_id": task_id, "chunk": i, "md5": md5, "filename": Filename}
            #             res = requests.post(url, data=params, files={'file': aLine}, headers=t_headers)
            #             print(res.text)
            #         i = i + 1
            # file.close()  # 关闭文件
            #
            # # #####################################
            # # # 请求merge接口，分段传入数据合并传入
            # # # 的数据
            # # #####################################
            # with open(Filename, "rb") as md5file:
            #     md5 = hashlib.md5(md5file.read()).hexdigest()
            # md5file.close()
            # print(md5)
            # url = baseUrl + "/upload/merge?task_id=" + task_id + "&md5=" + md5 + "&filename=" + Filename + ""
            # res = requests.get(url, headers=t_headers)
            # print(res.text)
    else:
        print("下载失败,错误原因是：")
        result = response.json()  # 返回值 json
        print(result)

