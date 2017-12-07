import urllib #用来解析url
import lxml
import lxml.html as lhtml
import pandas as pd
import numpy as np


#generate the urls which are needed to process
def gen_urls():
    urllist = ["https://www.ixl.com/ela/pre-k", "https://www.ixl.com/ela/kindergarten"]
    for i in range(1,13):
        url = "https://www.ixl.com/ela/grade-{}".format(i)
        urllist.append(url)
    return urllist


#定制化一下为我们后面制作表的时候服务
#这个是核心函数，围绕核心周边配置其他函数，就是一系列的get函数
#获取url中的信息本身并不复杂，主要是做成表的过程
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
    return html


#这个是get basic info，就是grade，grade的info
def get_g_info(url):
    urlp = url.split('/')
    urlp = urlp[-1]
    return urlp


#这里分别用lxml模块解析出了两个部分，一个是大点，然后是大点下面的小点
#其他页面结构也是这样的，所以倒不用担心这个无法被复用
#上面是各个小点的名称
def get_d_k_p(html0):
    tree = lhtml.fromstring(html0)
    td = tree.cssselect("a.skill-tree-skill-link")
    s_t_s_n = []
    for i in td:
        kp = str(i.text_content())
        s_t_s_n.append(kp)
    #下面是各个大点的名称
    tree0 = lhtml.fromstring(html0)
    td0 = tree0.cssselect("h2.skill-tree-skills-header")
    s_t_s_h = []
    for i in td0:
        kp0 = str(i.text_content())
        s_t_s_h.append(kp0)
    #这里的话是把各个大点和小点对应起来
    #下面的嵌套循环把lford变成了一个需要的列表套列表结构，等一下会转换成字典，然后生成数据框，再转置
    AZL = []
    [AZL.append(chr(i).upper())for i in range(97,123)]#生成了A-Z，这个是为了下一步做准备
    lford = list(map(list,list(zip(s_t_s_h,AZL))))#把列表zip对应之后可以被用来做对照依据
    for i in s_t_s_n:
        for j in lford:
            if i[0] == j[1]:
                j.append(i)
            else:
                pass
    #最后再把他们变成dataframe就可以了，这样就把所有得到的信息整理成了数据框和csv
    dict_f = {}
    for i in lford:
        dict_f[i[0]] = i[1:]
    df_f = pd.DataFrame.from_dict(dict_f, orient = "index").T
    df_f.drop(0, inplace = True)
    return df_f


#这个部分处理的是domian和knowledge_point到第一个可拼接长表，后面都链接到这个长表上
#这个函数好像有点小问题，会出现有些小知识点最后一个没有给归类到domain里面的情况，这个可能跟那个len有关
#问题找到了，都是每个domain里个数最多的那个最后一个会少掉，我想想这个逻辑怎么改
def get_d_k(df_f):
    df_final = pd.DataFrame()
    for i in range(len(df_f.columns)):
        df_f0 = pd.DataFrame(df_f.iloc[:,i])
        #下面的len+1是必须的，因为domain中最长一项总是丢失，但是+1也不用怕多出来的空值，因为下面会被drop掉
        s_fo = pd.Series(((df_f.iloc[:,i].name+"\n")*(len(df_f)+1)).split("\n")) #就是切成了多少个，问题应该在这里
        df_ff = pd.concat([s_fo,df_f0], axis = 1)
        df_ff.dropna(inplace = True) #这个地方为什么会产生空值。。。？
        df_ff.columns = ["domain","knowledge_point"]
        df_final = pd.concat([df_final,df_ff], axis = 0)
    df_final.reset_index(drop=True, inplace = True)
    return df_final


#借助改进过的函数，用info变量解决grade的问题
def get_grade(df_final,info):
    s_g = pd.Series(((info+"\n") * len(df_final)).split("\n"), name = "grade_level")
    df_final = pd.concat([df_final, s_g],axis = 1)
    df_final.dropna(inplace = True)
    return df_final


#这个是算present_times,各自定义一个函数，调用就好
def get_pt(df_final):
    df_kp = pd.DataFrame(df_final["knowledge_point"].value_counts())
    df_kp.reset_index(inplace = True)
    df_kp.columns = ["knowledge_point", "present_times"]
    df_final = pd.merge(df_final, df_kp, on = "knowledge_point", how = "inner")
    return df_final


#还差一个entry的
#entry这个的话，用drop_duplicate的方法，只保留最早，根据对应的grade，可以轻松算出来
#最后再合到一张表上，先把那些网页的名字写下来
def get_entry(df_final):
    #grade_level那列就是entry，因为取的是first，保留的
    #然后knowledge point作为考察依据
    df_cache = df_final.drop_duplicates(subset="knowledge_point")[["knowledge_point","grade_level"]]
    df_cache.rename({"grade_level":"entry"},axis = 1,inplace = True)
    df_ff = pd.merge(df_final, df_cache, on = "knowledge_point", how = "left")
    return df_ff


#直接写一个main函数
def main_p(urllist): #notice that the parameter should be a list
    #首先先用for循环把主要三列做出来
    df_final = pd.DataFrame()
    for url in urllist: #就分别调用一下那几个函数
        html = download(url) #先把html拿下来
        info = get_g_info(url) #然后把basic_info做好，用于后面制作表格
        df_f = get_d_k_p(html) #处理出两行一般表，最核心的两列，一个是domian，一个是kp,但是这个还要转换
        df_final0 = get_d_k(df_f) #转换成完整的domain和kp两列的表
        df_final0 = get_grade(df_final0, info) #这个是产生了一个带有grade的列表
        df_final = pd.concat([df_final, df_final0], axis = 0)
    df_final.reset_index(drop = True)
    #这个应该是整个表完成之后再调用这个函数计算总体的
    df_final = get_pt(df_final) #这个产生了一个加上present_time的列表，这个函数其实调用位置不应该在这里
    #还有要计算最早出现时间，也就是entry
    df_final = get_entry(df_final)
    return df_final


if __name__ == "__main__":
    urllist = gen_urls()
    data_final = main_p(urllist)
    data_final.to_csv("data_final.csv")



