import time
import utils
import requests
from bs4.element import *
from selenium import webdriver
from urllib import parse
import mongo_client
from config import *
from math_resolve import *


# Convert the img src to MathML
def resolve_mathml(src=''):
    url_decode = parse.unquote(src)
    return re.findall("<math.*math>", url_decode)[0]


# Get uuid from the img src
def get_uuid(src=''):
    name = src.split('/')[-1]
    return name.split('.')[0], name.split('.')[1]


def resolve_img_tag(tag):
    """
        图片标签存在三种格式：MathML png gif
        第一种为文本格式  后两种需要通过ocr识别
    :param tag:
    :return:
    """
    img_src = tag[SRC]
    if img_src.find(MATHML_TO_IMAGE) != -1:  # URL contains MathML then just resolve it
        return {MATH_ML: resolve_mathml(img_src)}, {}
    elif img_src.find(IMAGE) != -1:  # Simple url for png
        uuid, img_format = get_uuid(img_src)
        return {img_format: uuid}, {UUID: uuid, SRC: img_src, RESOLVED: False}
    else:
        return {}, {}


# Resolve the tag as a plain text
# HTML Tag is a tree, use DFS to travers
def resolve_tag(tag=Tag(name='')):
    """
        解析包含有图片和文本的标签，将标签解析为一个列表，每个元素为字典元素 {type: value}
        type: 文本类型 [plain_text, png, mathml, latex], value: 对应的值
    :param tag:
    :return:
    """
    plain_text = []
    url_map = []
    for child in tag.children:  # Traverse the children of tag
        if isinstance(child, NavigableString):  # NavigableString is a plain text, just append to plain_text
            plain_text.append({PLAIN_TEXT: str(child)})
        elif child.name == 'br':  # Tag <br>, append a new line
            pass
        elif child.name == 'img':  # Tag <img>, append the attribute 'src'
            png, image = resolve_img_tag(child)
            plain_text.append(png)
            if len(image) != 0:
                url_map.append(image)
            text, temp_map = resolve_tag(child)  # Call resolve_tag recursively
            plain_text += text
            if len(temp_map) != 0:
                url_map += temp_map
        elif isinstance(child, Tag):  # If current child is a tag, call resolve_tag recursively
            text, temp_map = resolve_tag(child)
            plain_text += text
            if len(temp_map) != 0:
                url_map += temp_map
    return plain_text, url_map


# 解析只包含单个子标签的的标签
def resolve_single_tag(tag=Tag(name='')):
    if tag.name == 'img':
        return resolve_img_tag(tag)
    elif isinstance(tag, NavigableString):
        return {PLAIN_TEXT: tag.text}, {}
    else:
        for child in tag.children:
            if isinstance(child, NavigableString):
                return {PLAIN_TEXT: str(child)}, {}
            elif child.name == 'img':
                return resolve_img_tag(child)
            else:
                return resolve_single_tag(child)
        return {}, {}


def resolve_tag_unclosed(tag=Tag(name='')):
    """
        解析未闭合的标签 <img> <img>  -->正确写法应该是 <img/><img/>
        此类标签会被看成父标签的一个字标签，解析的时候容易出错
    :param tag:
    :return:
    """
    text = []
    src_list = []
    if isinstance(tag, NavigableString):
        text.append({PLAIN_TEXT: str(tag)})
    elif tag.name == 'img':
        key, src = resolve_img_tag(tag)
        text.append(key)
        if len(src) != 0:
            src_list.append(src)
        for content in tag.contents:
            keys, src = resolve_tag_unclosed(content)
            text += keys
            src_list += src
    else:
        keys, src = resolve_tag(tag)
        text += keys
        src_list += src
    return text, src_list


def resolve_options(tag=Tag(name='')):
    """
        选项中可能存在多种格式的文本，因此保存为一个list
        如{'A': [{'png':'uuid'},{'mathml': 'ml'}, {'plain_text': '123'}]}
    :param tag:
    :return: options 选项
             src_map 选项中包含的图片
    """
    options = {}
    src_map = []
    if tag is None:
        return options, src_map
    for div in tag.contents[0].contents:
        option, temp = resolve_single_tag(div.contents[0])
        op = str(option[PLAIN_TEXT]).strip(' ').rstrip('.')
        value_tags = div.contents[1].contents
        for value_tag in value_tags:
            if isinstance(value_tag, NavigableString):
                options.update({op: [{PLAIN_TEXT: str(value_tag)}]})
            elif len(value_tag.contents) != 0:
                values, temp_map = resolve_tag_unclosed(value_tag)
                if len(temp_map) != 0:
                    src_map.append(temp_map)
                options.update({op: values})
            elif isinstance(value_tag, Tag):
                value, temp_map = resolve_single_tag(value_tag)
                if len(temp_map) != 0:
                    src_map.append(temp_map)
                options.update({op: [value]})
    return options, src_map


# 提取答案解析
def resolve_analysis(tag=Tag(name='')):
    analysis = {}
    src_list = []
    for item in tag.contents:
        pair, temp = resolve_single_tag(item.contents[0])
        key = pair[PLAIN_TEXT]
        key = str(key).replace('【', '').replace('】', '')
        value, img_src = resolve_tag(item.contents[1])
        analysis[key] = value
        if len(img_src) != 0:
            src_list += img_src
    return analysis, src_list


def resolve_message(message_tag=Tag(name='')):
    spans = message_tag.select("span")
    message = {}
    message["type"] = spans[0].text
    message["class"] = spans[1].text
    message["level"] = spans[2].text
    message["subject"] = spans[3].text
    return message


def update_url_resolved(question_list=[]):
    img_id_list = []
    for q in question_list:
        img_id_list.append(q[ID])
    mongo_client.update_url_resolved(img_id_list)


# 单选题解析
def resolve_single(filters):
    last = 0
    img_list = []
    question_list = []
    warn = True
    start_time = time.time()
    begin_time = start_time
    count = 0
    while True:
        url_list = mongo_client.load_unresolved_url(BATCH_SIZE, last, filters)
        count += len(url_list)
        if len(url_list) == 0:
            break
        last += BATCH_SIZE
        for item in url_list:
            if not item[RESOLVED]:  # False indicates current url has not been resolved yet
                try:
                    resp = requests.get(url=item['url'], headers=HEADERS)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    title_tag = soup.select_one("div .paper-question-title")
                    title_sequence, title_img_list = resolve_tag(title_tag)
                    if len(title_img_list) != 0:
                        img_list += title_img_list
                    options_tag = soup.select_one("div .paper-question-options")
                    option_sequence, option_img_list = resolve_options(options_tag)
                    if len(option_img_list) != 0:
                        img_list += option_img_list
                    analyze_tag = soup.select_one("div .paper-analyize")
                    analysis_sequence = {}
                    analysis_img_list = []
                    analyze_text = analyze_tag.text
                    if utils.contains_str(analyze_text, '显示答案解析'):
                        print("Warning! You have not login! Answer is invisible!")
                        analysis_sequence[FETCHED] = False
                    elif utils.contains_str(analyze_text, '限制'):
                        if warn:
                            print("Sorry! You have run out of the accessing times of answer!")
                            warn = False
                        analysis_sequence[FETCHED] = False
                    else:
                        analysis_sequence, analysis_img_list = resolve_analysis(analyze_tag)
                        analysis_sequence[FETCHED] = True
                    if len(analysis_img_list) != 0:
                        img_list += analysis_img_list

                    message_tag = soup.select_one("div .paper-message-attr")
                    question_message = resolve_message(message_tag)

                    question_data = {"id": item["id"], "title": title_sequence, "options": option_sequence}
                    question_data.update(question_message)
                    question_data.update(analysis_sequence)
                    question_list.append(question_data)
                except Exception as ex:  # 捕获所有异常，出错后单独处理，避免中断
                    print(ex)
                    print("Resolve failed id=[%s]" % item["id"])
                if len(question_list) == QUESTION_BATCH_SIZE:
                    save_questions(img_list, question_list, start_time, time.time())
                    start_time = time.time()
        if len(question_list) > 0:
            save_questions(img_list, question_list, start_time, time.time())
    print("Resolved [%d] questions taken %.2f s" %(begin_time, time.time() - begin_time))


def save_questions(img_list, question_list, start_time, end_time):
    print("Save %d questions to mongo takes %.2f s" % (len(question_list), end_time - start_time))
    if not mongo_client.insert_many(QUESTION_DETAILS, question_list):
        print("Insert batch questions failed. Try to insert one by one")
        for q in question_list:
            if not mongo_client.insert_one(QUESTION_DETAILS, q):
                print("Insert question[id=%s] failed. Try to insert one by one" % q[ID])
    update_url_resolved(question_list)
    question_list.clear()
    if len(img_list) != 0:
        if not mongo_client.insert_many(COLLECTION_IMAEG, img_list):
            print("Insert batch images failed. Try to insert one by one")
            for img_src in img_list:
                if not mongo_client.insert_one(COLLECTION_IMAEG, img_src):
                    print("Insert image[uuid=%s] failed. Try to insert one by one" % img_src[UUID])
        img_list.clear()


# Return False when get empty cookies or contains expired cookie
def is_valid_cookies(cookies=[]):
    if len(cookies) == 0:
        return False
    for cookie in cookies:
        if cookie['name'] == '_gat_gtag_UA_137517687_1':
            continue
        if 'expiry' in cookie.keys() and cookie['expiry'] < time.time():
            return False
    return True


def get_cookies(login_with_wechat=False, account=''):
    """
        get cookies after logining in 51jiaoxi and return cookies as a string.
        you should login in this site mannually so this function will wait for pressing a key after you login in this site.
        WARNING: you should download chromedriver and move this application to the current floder.
        If you don't have this application, you can access https://chromedriver.chromium.org/,
        check your chrome version and download corresponding version's chromedriver.
    """
    cookies = mongo_client.load_cookies(account)
    if is_valid_cookies(cookies):
        return cookies
    # with webdriver.Chrome(executable_path=r'./chromedriver') as driver:
    with webdriver.Chrome() as driver:
        driver.get(login_url)
        # waiting for logining in this site and press any key to continue
        if login_with_wechat:
            print("Please scan two-dimension code to login! And press any key to continue!")
            input()
        else:
            driver.find_element_by_css_selector("div[class='phone login-way wechat-leave']").click()
            driver.find_element_by_id('login-auth-phone').send_keys(phone_number)
            driver.find_element_by_id('login-auth-password').send_keys(password)
            driver.find_element_by_css_selector('div[class="submit"]').click()
            time.sleep(0.5)
            error_msg = driver.find_element_by_css_selector("span[class='alert-message error']").text
            if error_msg != "":
                print(error_msg)
                exit(1)
        cookies = driver.get_cookies()
        mongo_client.insert_or_update_cookies({ACCOUNT: account, COOKIES: cookies})
        return cookies


def refresh_cookies(login_with_wechat=False):
    cookies = get_cookies(login_with_wechat, phone_number)
    cookies_str = ''
    for cookie in cookies:
        cookies_str += str(cookie['name']) + '=' + str(cookie['value']) + ';'
    HEADERS[COOKIE] = cookies_str


if __name__ == '__main__':
    refresh_cookies(False)
    filters = {"type": "单选题", }
    resolve_single(filters)
