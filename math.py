# coding=utf-8

import sys
import time

from selenium import webdriver


def is_elem_exist(xpath_str, element):
    # 判断是否存在元素
    try:
        element.find_element_by_xpath(xpath_str)
        return True
    except:
        return False


# --------------------------------------需要初始化的值--------------------------------------------
# 爬取的页面链接，一类题的最小知识点为一个页面
url = 'http://zujuan.51jiaoxi.com/#/paperFrontend/manual?stage_id=3&subject_id=3&knowledge_id=2530'
# url存入文件路径
path = r'urllist1.csv'
# ----------------------------------------------------------------------------------------------



# 调用webdriver
driver = webdriver.Chrome()
driver.get(url)
# 由于代码不够完善，还需要手动点击
time.sleep(1)
# html = driver.execute_script("return document.documentElement.outerHTML")
# with open("index.html", "w") as f:
driver.maximize_window()
for i in driver.find_elements_by_xpath(
        "//div[@class='manual-main-right-top-item'][1]//li[1]/following-sibling::li"):  # 切换 选择题/填空题/解答题......
    i.click()
    time.sleep(1)
    m = 0
    while m < 100:
        m += 1
        print(m)
        for j in driver.find_elements_by_link_text('查看解析'):
            q_url = j.get_attribute('href')
            with open(path, 'a') as f:
                f.write(q_url)
                f.write('\r')
                f.close()

        if is_elem_exist('//li[@class=\"btn-next\"]', driver):
            driver.find_element_by_xpath('//li[@class="btn-next"]').click()
            time.sleep(1)
        else:
            break
driver.quit()

# 2.提取url，爬取数据
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pyquery import PyQuery as pq
from collections import OrderedDict


# 数据写入文件的函数
def w_to_f(data, w_path):
    str_data = json.dumps(data, indent=4, ensure_ascii=False)
    # str_data=re.sub(r'(\\r\\n)+|(\\n)+|(\\t)+',string=str_data,repl="")
    with open(w_path, "a", encoding='utf-8') as f:
        f.write(str_data)
        f.write(',')
        f.write('\r')
    f.close()


# -------------------------------------------需要初始化的值------------------------------------------------
# 读取url的文件路径
r_path = r'爬虫\爬取教习网\urllist\urllist1.csv'

# 保存爬取数据的文件路径
wt_path = r'爬虫\爬取教习网\or_data\or_data_1.json'

# headers，目前还没有把自动登录获取cookie的方式调试出来，所以需要手动添加cookie
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36',
    'Cookie': '_ga=GA1.2.42473173.1588848496; paperId=0; Hm_lvt_e933c796aa676cbb0afa2bf2bee228fd=1591541974,1591617285,1591709811,1591973405; _gid=GA1.2.1948639972.1591973405; filters=1%2C3; _gat_gtag_UA_137517687_1=1; Hm_lpvt_e933c796aa676cbb0afa2bf2bee228fd=1591980834; wechat_flag=eyJpdiI6IjduWnVDV040b3JtVk92Q3laaUl2TEE9PSIsInZhbHVlIjoiVHg5VFd3QXo2RFRKSjVGREJ1OHZXRVIzSHBUWWQ1WEM4aUNVdjlEdlFvN2s0bFZWS2M0T2hSZWNjMlZlSTFCNyIsIm1hYyI6IjNlZmNmNDQ2ZmU5OTJlYWE5YWU0YzBlYTcwZGM1NDc1NjgyMDg5OTRlZjRlNDIzYTlmYjFjMDE0ZGQxMGUwNWMifQ%3D%3D; XSRF-TOKEN=eyJpdiI6IjF3V29ReHk2NzlCeHpKek9vMXlIeVE9PSIsInZhbHVlIjoicjhHQ3J0WWllXC8xTjRRN3dsWG01TU54d2ZMN2F1dmJrbENMaWZEREVXM1ZsRnA5YVVvd1ZoZW5aeE01WHhcL2ROIiwibWFjIjoiMzhlOTVlOTExYWIzMjQ3OTE4OTM3NGNkOTQ1NGQzMTFhODMyZTFkNzcwZDlkZDQyNDFlOGM5YjFmNTY1YjJjMyJ9; _session=eyJpdiI6ImxFMGdZR1h6dVgzNXhPR3U3SFI1SEE9PSIsInZhbHVlIjoib1l0V0dCWWJxZkprc1crXC9mOGlSbVp6XC92UnVxMkpicWFHeDlKdWFvcDZRcUFLZFdxVVVlTG90XC9JQUU5RTZYViIsIm1hYyI6ImNhNzNjNjU2YzYyM2M1ZDczMTUwNGNmMGYxZjQxNDkzNmI5YmZlZjM1ZGQ4YTMwMGVmOWVkZGJjMmU2YWI3NTIifQ%3D%3D'}

max_num = 35  # 爬到第max_num个链接结束爬取
min_num = 0  # 从第min_num个链接开始爬取
m = 0  # 第m个链接

# max和min相差35，每爬取35道题需要更换账号
# 这个网站爬数据必须要登录账号，手机号注册账号+绑定微信的情况下，一个账号有35道题目免费查看/天，超过限制也无法爬取到数据，所以需要准备多个账号来爬题目
# ---------------------------------------------------------------------------------------------------------------
url_list = pd.read_csv(r_path, sep=',', header=None)
print(len(url_list))
url_list = url_list.drop_duplicates(keep='first')  # 去重
print(len(url_list))

for url in url_list[0]:
    m += 1
    # 由于每个账号限制爬取35道，所以需要跳过已爬、和超过时结束循环
    if m > max_num:
        break
    elif m <= min_num:
        continue
    else:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        div = soup.find('div', class_='paper_filter_bd')
        # print(div)
        pqdiv = pq(str(div))
        ul = pqdiv('ul').eq(0)
        # 一道题的数据都在li标签中，这段程序主要是保存这段源码
        li = ul.find('li')
        json_data = OrderedDict({'data': str(li)})
        w_to_f(json_data, wt_path)

# 3.从源码中初步分离出题目、答案、解析等
# 分离出来的数据还是源码形式
from pyquery import PyQuery as pq
import pandas as pd
import re


def ele_is_r(element, tag):
    # 在tag下找element，判断有没有这个element
    if tag.find(element):
        return 1
    else:
        return 0


# 数据写入文件
def w_to_f(data, w_path):
    str_data = json.dumps(data, indent=4, ensure_ascii=False)
    # str_data=re.sub(r'(\\r\\n)+|(\\n)+|(\\t)+',string=str_data,repl="")
    with open(w_path, "a", encoding='utf-8') as f:
        f.write('    ')
        f.write(str_data)
        f.write(',')
        f.write('\r')
    f.close()


# -----------------------------------需要初始化的值------------------------------
# 读取的原数据文件路径
r_path = r'or_data_1.json'

# 写入数据的文件
path = r're_data_1.json'

# -----------------------------------------------------------------------------
with open(path, 'a') as f:
    f.write('[')
    f.write('\r')
f.close()
# 读取原数据
datas = pd.read_json(r_path, encoding='utf8')
print(datas.head())
m = 0
for q_data in datas['data']:
    m += 1
    json_data = {'题号': m, '题目': [], '选项': [], '答案': [], '解析': '', '题型': '', '知识点': '', '难度': ''}
    q_text = pq(q_data)
    # ----------------------------------题目------------------------------------------
    ques = q_text('div .paper-question').eq(0)
    q_title = ques('div .paper-question-title')
    title = [str(q_title)]
    # 判断是否有小题
    if ques('div .paper-subquestion-title'):
        for ele in ques('div .paper-subquestion-title').items():
            title = title + [str(ele)]
    json_data['题目'] = title
    # 如果上面的方法得到的题目是空，就运行下面的方法
    if json_data['题目'] == [""]:
        q_title = q_text.find('div .paper-question-title')
        title = [str(q_title)]
        if ele_is_r('div .paper-subquestion-title', q_text):
            for ele in q_text.find('div .paper-subquestion-title').items():
                title = title + [str(ele)]
        json_data['题目'] = title
    # --------------------------------------------------------------------------------

    # ---------------------------------选项--------------------------------------------
    if ques('div .paper-question-options'):
        q_op = ques('div .paper-question-options')
        i = q_op.children('div')
        for op_item in i.children('div').items():
            json_data['选项'] = json_data['选项'] + [str(op_item)]
            # print('选项：',op_item)
    if json_data['选项'] == []:
        if ele_is_r('div .paper-question-options', q_text):
            q_op = q_text.find('div .paper-question-options')
            i = q_op.children('div')
            for op_item in i.children('div').items():
                json_data['选项'] = json_data['选项'] + [str(op_item)]
    # --------------------------------------------------------------------------------

    # --------------------------------分析-----------------------------------------------
    q_anlyz = q_text.children('div .paper-analyize')
    for anlyz_item in q_anlyz('div .paper-analyize-right').items():
        if re.search(r'<div.*?paper-answer">', str(anlyz_item)):
            json_data['答案'] = [str(anlyz_item)]
        elif re.search(r'<div.*?paper-centre">', str(anlyz_item)):
            json_data['知识点'] = str(anlyz_item)
        else:
            json_data['解析'] = str(anlyz_item)
    # 如果答案是空的，用下面的方法
    if json_data['答案'] == []:
        anlyz_ans = []
        for anlyz_item in q_text('div .paper-subquestion-answer-right').items():
            anlyz_ans = anlyz_ans + [str(anlyz_item)]
        json_data['答案'] = anlyz_ans
    # --------------------------------------------------------------------------------------

    # ----------------------------------标签---------------------------------------------
    q_attr = q_text('div .paper-message-attr').eq(0)
    sp = q_attr.children('span')
    json_data['题型'] = str(pq(sp[0]).text())
    json_data['难度'] = str(pq(sp[2]).text())
    # ----------------------------------------------------------------------------------
    print(m)
    # 将数据写入文件
    w_to_f(json_data, path)
with open(path, 'a') as f:
    f.write(']')
f.close()

# 4.整理数据，得到干净的数据
# encoding:utf-8
import requests
import json
from pyquery import PyQuery as pq
import re


# 用re清理数据
def re_clean(string1):
    string1 = re.sub('<sub>', repl='_', string=string1)  # 匹配上、下标
    string1 = re.sub('<sup>', repl='^', string=string1)
    string1 = re.sub('(</sub>|</sup>)', repl="", string=string1)
    string1 = re.sub(r'<u>    \d{1}    </u>', repl="(____)", string=string1)  # 匹配填空题空格
    string1 = re.sub(r'<.*?>|(\n)+|(\t)+|( )+', string=string1, repl="")
    string1 = re.sub(r'&lt;', repl="<", string=string1)  # 大于小于符号
    string1 = re.sub(r'&gt;', repl=">", string=string1)
    return string1


# 用re匹配<img>标签，即图片
def re_find_mathimg(string1):
    img = re.findall(r'<img class="mathml" .*?/>', string1)  # 匹配公式链接
    if img:
        for i in img:
            im = pq(i)
            i_url = im.attr('src')
            # print(i_url)
            index_str = save_img(i_url)
            index_str = 'png_' + index_str
            string1 = re.sub(r'<img class="mathml" .*?/>', repl=index_str, string=string1, count=1)
    img = re.findall(r'<img.*?/>', string1)  # 匹配图片链接
    if img:
        for i in img:
            im = pq(i)
            if im.attr('src'):
                i_url = im.attr('src')
                index_str = save_img(i_url)
                index_str = 'png_' + index_str
                string1 = re.sub(r'<img.*?/>', repl=index_str, string=string1, count=1)
            else:
                index_str = ""
                string1 = re.sub(r'<img.*?/>', repl=index_str, string=string1, count=1)
    return string1


# 数据写入文件
def w_to_f(data, w_path):
    str_data = json.dumps(data, indent=4, ensure_ascii=False)
    # str_data=re.sub(r'(\\r\\n)+|(\\n)+|(\\t)+',string=str_data,repl="")
    with open(w_path, "a", encoding='utf-8') as f:
        f.write('    ')
        f.write(str_data)
        f.write(',')
        f.write('\r')
    f.close()


# 保存图片
def save_img(img_url):
    global img_num
    img_num += 1
    # 图片保存地址
    img_save_pace = r'爬虫\爬取教习网\picture\picture_1' + "\\" + str(img_num) + ".png"  # 保存路径
    r = requests.get(img_url)
    with open(img_save_pace, 'wb') as f:
        f.write(r.content)
    return str(img_num)


# ------------------------------------------需要初始化的值----------------------------
img_num = 1100000  # 图片编号

# 读取数据的文件路径
r_path = r'爬虫\爬取教习网\re_data\re_data_1.json'

# 写入数据的文件路径
w_path = r'爬虫\爬取教习网\final_data\final_data_1.json'

with open(w_path, 'a') as f:
    f.write('[')
    f.write('\r')
f.close()

# 读取数据
f = open(r_path, 'r', encoding="utf-8")
data3 = json.load(f)
n = 0
print(len(data3))
for data in data3:
    json_data = {'题号': n, '题目': [], '选项': [], '答案': [], '解析': '', '题型': data['题型'], '知识点': '', '难度': data['难度']}
    n += 1
    print(n)
    # ------------------------------题目---------------------------------
    for string in data['题目']:
        s = re_find_mathimg(string)
        s = re_clean(s)
        json_data['题目'] = json_data['题目'] + [s]
    # -------------------------------选项--------------------------------
    if data['选项'] != []:
        for string in data['选项']:
            s = re_find_mathimg(string)
            s = re_clean(s)
            json_data['选项'] = json_data['选项'] + [s]
    # ------------------------------解析------------------------------
    string = data['解析']
    s = re_find_mathimg(string)
    s = re_clean(s)
    json_data['解析'] = s
    # ------------------------------答案------------------------------
    for string in data['答案']:
        s = re_find_mathimg(string)
        s = re_clean(s)
        json_data['答案'] = json_data['答案'] + [s]
    # -----------------------------知识点----------------------------
    string = data['知识点']
    s = re_find_mathimg(string)
    s = re_clean(s)
    json_data['知识点'] = s

    # 写入数据
    w_to_f(json_data, w_path)

with open(w_path, 'a') as f:
    f.write(']')
f.close()
