# Uploader

主要完成本地文件上传到服务器的简单脚本

这里有单个单个的文件上传，也有多个文件一起传的文件

这里解决了一个并发上传文件为了线程安全需要加锁，但是也可以使用localthread，各自使用本地线程资源，极大概率不会造成线程多读多写
可以查看uploaderfast.py
