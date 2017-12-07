import pandas as pd
import numpy as np
import pytesseract as pt
from PIL import Image #pillow这个包怪怪的。。。只能叫他PIL。。。#PIL其实也用不上，pytesseract似乎有点麻烦
import os
import subprocess
import urllib #用来解析url
import lxml
import lxml.html as lhtml
import re
import time

#得到urllist，方便获得所有网址
def gen_urls():
    urllist = ["https://www.ixl.com/ela/pre-k", "https://www.ixl.com/ela/kindergarten"]
    for i in range(1,13):
        url = "https://www.ixl.com/ela/grade-{}".format(i)
        urllist.append(url)
    return urllist

#根据urllist，可以先生成一个次级目录，根据url最后的几个来
def create_folder(u_list):
    d_list = []
    for i in u_list:
        dir0 = i.split("/")[-1] #就按照这个来生成图片的目录
        d_list.append("E:/img/" + dir0)
        os.makedirs("E:/img/" + dir0)
    return d_list
#生成好了次级目录要被留下来，等一下作为下载好的图片的依据
#如果有需要分类的话在这里加一个I/O路径编程可以解决问题
#不过似乎也不用，毕竟有规律，这个不管了，问题不大

#定制化一下为我们后面制作表的时候服务
def download(url):
    print("Downloading:{}".format(url))
    #伪装一下浏览器header，伪装一下
    #其实还有禁用cookie的做法，那个也很强
    header = {'User-Agent':'Mozilla/5.0 \
    (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6)\
    Gecko/20091201 Firefox/3.5.6'}
    request0 = urllib.request.Request(url, headers = header)
    try:
        html = urllib.request.urlopen(request0).read()
    except urllib.error.URLError as e:
        print("Download error", e.reason)
        html = None
        download(url)
    return html

#为了加入到迭代里面，我需要新加一个东西
def d_img_s(url, folder_name,name):
    print("Downloading:{}".format(url))
    #伪装一下浏览器header，伪装一下
    #其实还有禁用cookie的做法，那个也很强
    header = {'User-Agent':'Mozilla/5.0 \
    (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6)\
    Gecko/20091201 Firefox/3.5.6'}
    request0 = urllib.request.Request(url, headers = header)
    try:
        conn = urllib.request.urlopen(request0)
        name = "E:/img/" + folder_name + "/" + str(name) + ".png"
        with open(name,"wb") as f:
            f.write(conn.read())
        print("png saved")
    except:  #如果遇到下载错误，不选择直接结束，而是回头重新执行上一个函数
        d_img_s(url,folder_name,name)
    return 0

#这个出来的是真正的unique的图片地址列表
def get_fullscreen_v(url):
    html = download(url)
    html = html.decode("utf-8")
    pattern = r'(?<=<section).+'
    section = re.compile(pattern).search(html).group()
    pattern = r'''(?<=data-full-screenshot-versions="\[)&quot;\w+&quot;,&quot;\w+&quot;,&quot;\w+&quot;,&quot;\w+&quot;\]'''
    # 只要是特指的，这个正则表达式就没问题，可以被写出来，但是自动化更好，不行我手写了
    # 手写吧...自动化晚点再说，反正数据结构固定。。。
    result = re.compile(pattern).findall(section)
    result_final = ''

    for i in result:
        result_final = i + result_final

    pattern = r"(?<=&quot;)\w+"
    result_final = re.compile(pattern).findall(result_final)
    result_final = list(map(lambda x: "https://www.ixl.com/screenshot/" + x + ".png", result_final))
    result_final.reverse()#这个反向是必须的，因为上面处理之后url的顺序全反过来了，需要再反过来
    return result_final


def get_png(url):
    png_list = get_fullscreen_v(url)
    j = 1
    for i in png_list:
        try:
            d_img_s(i,url.split("/")[-1], j)
            j+=1
            if j > len(png_list):
                j = 1
            else:
                pass
        except: #由于经常发生EOL的问题，所以一旦EOL也继续执行同样的操作，但是这个操作并没用，感觉不仅仅是在这里
            #d_img_s里面采取了递归写法，可以解决这个问题了，但是即使不断尝试有时候也解决不了问题，公司的SSL问题
            #用递归的思路解决问题是没错的
           get_png(url)
        print(j)
        print("download finished")
        time.sleep(2) #因为这个爬虫比较简单，所以delay就写这么多吧，到时候正式爬取的时候会加这个的，先部署
    return 0

#main函数的设定是需要考虑的，
if __name__ == "__main__":
    u_list = gen_urls()
    create_folder(u_list)#先生成一下文件夹
    for url in u_list:
        get_png(url)
