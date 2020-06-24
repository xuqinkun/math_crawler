import time
from threading import Thread
from urllib import parse

import requests
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from bs4.element import *
from selenium import webdriver

import mongo_client as db_client
import utils
from config import *

def resolve_mathml(src=''):
    """
    Convert the img src to MathML
    :param src: img src
    :return: MathML
    """
    url_decode = parse.unquote(src)
    return re.findall("<math.*math>", url_decode)[0]


def get_uuid(src=''):
    """
    Get uuid from the img src
    :param src: img src
    :return: uuid, picture format
    """
    name = src.split('/')[-1]
    return name.split('.')[0], name.split('.')[1]


def resolve_img_tag(tag=Tag(name="")):
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
        # print(tag)
        uuid, img_format = get_uuid(img_src)
        return {img_format: uuid}, {UUID: uuid, SRC: img_src, RESOLVED: False}
    else:
        return {}, {}


def resolve_tag(tag=Tag(name='')):
    """
        解析包含有图片和文本的标签，将标签解析为一个列表，每个元素为字典元素 {type: value}
        type: 文本类型 [plain_text, png, mathml, latex], value: 对应的值
    :param tag: Page element
    :return: Text, Image list
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

def resolve_sub_question(tag=Tag(name='')):
    """
        解析包含有图片和文本的标签，将标签解析为一个列表，每个元素为字典元素 {type: value}
        type: 文本类型 [plain_text, png, mathml, latex], value: 对应的值
    :param tag: Page element
    :return: Text, Image list
    """
    subtags = tag.select("div[class=paper-subquestion-title]")
    plain_text = []
    url_map = []
    for child in subtags:  # Traverse the subquestions of tag
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

def resolve_sub_analysis(tag=Tag(name='')):
    subtags = tag.select("div[class=paper-subquestion-answer]")
    plain_text = {"答案":[]}
    url_map = []
    for child in subtags:  # Traverse the children of tag
        img_src = []
        pair, temp = resolve_single_tag(child.contents[0])
        key = pair[PLAIN_TEXT]
        key = str(key).replace('【', '').replace('】', '')
        value, img_src = resolve_tag(child.contents[1])
        plain_text[key] += value
        url_map += img_src
    return plain_text,url_map

def resolve_single_tag(tag=Tag(name='')):
    """
    解析只包含单个子标签的的标签
    :param tag:
    :return: Text, Image info
    """
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
                    src_map += temp_map
                options.update({op: values})
            elif isinstance(value_tag, Tag):
                value, temp_map = resolve_single_tag(value_tag)
                if len(temp_map) != 0:
                    src_map.append(temp_map)
                options.update({op: [value]})
    return options, src_map


def resolve_analysis(tag=Tag(name='')):
    """
    提取答案解析
    :param tag:
    :return: Analysis text, Image list
    """
    analysis = {}
    src_list = []
    for item in tag.contents[0]:
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


def update_url_resolved(question_list):
    url_id_list = []
    for q in question_list:
        url_id_list.append(q[ID])
    db_client.update_url_resolved(url_id_list)


def save_questions(thread_name, img_list, question_list, start_time, end_time):
    print("Thread[%s] save %d questions to DB takes %.2fs" % (thread_name, len(question_list), end_time - start_time))
    if not db_client.insert_many(QUESTION_DETAILS, question_list):
        print("Thread[%s] insert batch questions failed. Try to insert one by one", thread_name)
        for question in question_list:
            if not db_client.insert_one(QUESTION_DETAILS, question):
                print("Thread[%s] insert question[id=%s] failed. Try to insert one by one" % (thread_name, question[ID]))
    update_url_resolved(question_list)
    question_list.clear()
    if len(img_list) != 0:
        if not db_client.insert_many(COLLECTION_IMAGE, img_list):
            print("Thread[%s] inserted batch images failed. Try to insert one by one", thread_name)
            for img_src in img_list:
                if not db_client.insert_one(COLLECTION_IMAGE, img_src):
                    print("Thread[%s] inserted image[uuid=%s] failed. Try to insert one by one" % (thread_name, img_src[UUID]))
        img_list.clear()


def is_valid_cookies(cookies):
    """
    :param cookies:
    :return: Return False when get empty cookies or contains expired cookie, otherwise return True
    """
    if len(cookies) == 0:
        return False
    for cookie in cookies:
        if cookie['name'] == '_gat_gtag_UA_137517687_1':
            continue
        if 'expiry' in cookie.keys() and cookie['expiry'] < time.time():
            return False
    return True


def validate_tag(tag, url):
    if tag is None:
        print("Resolved failed for url[%s]" % url)
        return False
    else:
        return True


class Task(Thread):
    def __init__(self, thread_id=0, thread_nums=1, question_type='', criteria=None,
                 account=None, use_gui=False, max_size=1000, phantomjs_path=''):
        """
        :param thread_id
        :param question_type:
        :param criteria: Extra filters for query
        :param account:  Account info, phone number and password
        :param use_gui: Use gui chrome to log in
        :param max_size: Max questions size dispatched to this thread
        """
        Thread.__init__(self, name="Crawler-" + str(thread_id))
        self.id = thread_id
        self.thread_nums = thread_nums
        self.type = question_type
        self.account = account
        self.use_gui = use_gui
        self.max_size = max_size
        self.criteria = criteria
        self.headers = HEADERS.copy()
        self.phantomjs_path = phantomjs_path

    def run(self):
        if self.type == SINGLE_CHOICE:
            criteria = {"type": self.type}
            if self.criteria is not None:
                criteria.update(self.criteria)
            self.refresh_cookies()
            self.resolve_single(criteria)
        elif self.type == FILL_BLANKS:
            criteria = {"type": self.type}
            if self.criteria is not None:
                criteria.update(self.criteria)
            # self.refresh_cookies()
            self.resolve_blank(criteria)
        elif self.type == COMPUTATION:
            criteria = {"type": self.type}
            if self.criteria is not None:
                criteria.update(self.criteria)
            # self.refresh_cookies()
            self.resolve_computation(criteria) 
        elif self.type == SYNTHESIS:
            criteria = {"type": self.type}
            if self.criteria is not None:
                criteria.update(self.criteria)
            # self.refresh_cookies()
            self.resolve_synthesis(criteria)


    def refresh_cookies(self):
        """
            Get cookies after logining in 51jiaoxi and return cookies as dict list.
            GUI: If false, you should provide phone and password to login automatically.
                 If true, you will login manually to continue.
            params: A dict, if GUI is false, params['phone'] and params['password'] should exists.
            WARNING: You should download chromedriver and move this application to the current floder.
                     If you don't have this application, you can access https://chromedriver.chromium.org/,
                     check your chrome version and download corresponding version's chromedriver.
            WARNING: You should download phantomjs and move this application to the current floder.
                     If you don't have this application. you can access https://phantomjs.org/download.html,
                     check your system and download corresponding version's phantomjs.
        """
        cookies = db_client.load_cookies(self.account[PHONE])
        if not is_valid_cookies(cookies):
            if not self.use_gui:
                driver = webdriver.PhantomJS(executable_path=self.phantomjs_path)
                # driver = webdriver.Chrome(executable_path='D:\\Tools\\ChromeDriver\\chromedriver.exe')
                driver.get(login_url)
                time.sleep(1)
                driver.maximize_window()
                time.sleep(1)
                driver.find_element_by_css_selector('div.phone.login-way.wechat-leave').click()
                driver.find_element_by_id('login-auth-phone').send_keys(self.account[PHONE])
                driver.find_element_by_id('login-auth-password').send_keys(self.account['password'])
                driver.find_element_by_css_selector('button.login-button.jx-button').click()
                time.sleep(1)
                error_msg = driver.find_element_by_css_selector("span[class='alert-message error']").text
                if error_msg != '':
                    print(error_msg)
                    exit(1)
            else:  # 使用微信扫码登录
                driver = webdriver.Chrome()
                driver.get(login_url)
                print("Please scan two-dimension code to login! And press any key to continue!")
                input()
            cookies = driver.get_cookies()
            db_client.insert_or_update_cookies({PHONE: self.account[PHONE], COOKIES: cookies})
        cookies_str = ''
        for cookie in cookies:
            cookies_str += str(cookie['name']) + '=' + str(cookie['value']) + ';'
        self.headers[COOKIE] = cookies_str
        return True

    def resolve_single(self, criteria):
        last = 0
        img_list = []
        question_list = []
        warn = True
        start_time = time.time()
        begin_time = start_time
        count = 0
        while count < self.max_size:
            offset = last + BATCH_SIZE * self.id
            url_list = db_client.load_unresolved_url(BATCH_SIZE, offset, criteria)
            print("Thread[%s] start to fetch [%d] questions" % (self.name, BATCH_SIZE))
            # url_list = db_client.load_url_by_id(['1901554'])
            count += len(url_list)
            last += BATCH_SIZE * self.thread_nums
            if len(url_list) == 0:
                break
            for item in url_list:
                if not item[RESOLVED]:  # False indicates current url has not been resolved yet
                    question_url = item['url']
                    try:
                        resp = requests.get(url=question_url, headers=self.headers)
                        if resp.status_code != requests.codes.ok:
                            print("Resolved failed for url[%s] status_code[%d]" % (question_url, resp.status_code))
                            continue
                        soup = BeautifulSoup(resp.text, 'html.parser')

                        # Resolve title
                        title_tag = soup.select_one("div[class=paper-question-title]")
                        if not validate_tag(title_tag, question_url):  # Skip tag which resolved failed
                            continue
                        title_sequence, title_img_list = resolve_tag(title_tag)

                        # Resolve options
                        options_tag = soup.select_one("div[class=paper-question-options]")
                        if not validate_tag(options_tag, question_url):  # Skip tag which resolved failed
                            continue
                        option_sequence, option_img_list = resolve_options(options_tag)

                        # Resolve analysis
                        analyze_tag = soup.select_one("div[class=paper-analyize-wrap]")
                        if not validate_tag(analyze_tag, question_url):  # Skip tag which resolved failed
                            continue
                        analyze_text = analyze_tag.text
                        analysis_sequence = {}
                        analysis_img_list = []
                        if utils.contains_str(analyze_text, '显示答案解析'):
                            print("Warning! You[%s] have not login! Answer is invisible! Try to refresh cookies..." % self.name)
                            if self.refresh_cookies():
                                print("Thread[%s] refresh cookies success!" % self.name)
                            analysis_sequence[FETCHED] = False
                        elif utils.contains_str(analyze_text, '限制'):
                            if warn:
                                print("Sorry! Thread[%s] has run out of the accessing times for analysis!" % self.name)
                                warn = False
                            analysis_sequence[FETCHED] = False
                        else:
                            analysis_sequence, analysis_img_list = resolve_analysis(analyze_tag.contents[0])
                            analysis_sequence[FETCHED] = True

                        message_tag = soup.select_one("div[class=paper-message-attr]")
                        question_message = resolve_message(message_tag)

                        question_data = {ID: item[ID], TITLE: title_sequence, OPTIONS: option_sequence}
                        question_data.update(question_message)
                        question_data.update(analysis_sequence)
                        question_list.append(question_data)

                        # 所有标签解析成功后才把图片存入数据库
                        # if len(title_img_list) != 0:
                        #     img_list += title_img_list
                        # if len(option_img_list) != 0:
                        #     img_list += option_img_list
                        if len(analysis_img_list) != 0:
                            img_list += analysis_img_list

                    except Exception as ex:  # 捕获所有异常，出错后单独处理，避免中断
                        print(ex)
                        print("Thread[%s] resolve failed id=[%s] url=[%s]" % (self.name, item[ID], question_url))
                    if len(question_list) == QUESTION_BATCH_SIZE:
                        save_questions(self.name, img_list, question_list, start_time, time.time())
                        start_time = time.time()
            if len(question_list) > 0:
                save_questions(self.name, img_list, question_list, start_time, time.time())
        print("Thread[%s] finished resolving [%d] questions taken %.2fs"
              % (self.name, count, time.time() - begin_time))
    
    def resolve_blank(self, criteria):
        last = 0
        img_list = []
        question_list = []
        warn = True
        start_time = time.time()
        begin_time = start_time
        count = 0
        while count < self.max_size:
            offset = last + BATCH_SIZE * self.id
            url_list = db_client.load_unresolved_url(BATCH_SIZE, offset, criteria)
            print("Thread[%s] start to fetch [%d] questions" %(self.name, BATCH_SIZE))
            # url_list = ["http://www.51jiaoxi.com/question-477458.html"]
            # url_list = db_client.load_url_by_id(['477458'])
            # print(url_list)
            count += len(url_list)
            last += BATCH_SIZE * self.thread_nums
            if len(url_list) == 0:
                break
            for item in url_list:
                if not item[RESOLVED]:  # False indicates current url has not been resolved yet
                    try:
                        question_url = item['url']
                        resp = requests.get(url=question_url, headers=self.headers)
                        if resp.status_code != requests.codes.ok:
                            print("Resolved failed for url[%s] status_code[%d]" % (question_url, resp.status_code))
                            continue
                        soup = BeautifulSoup(resp.text, 'html.parser')

                        # Resolve title
                        title_tag = soup.select_one("div[class=paper-question-title]")
                        if not validate_tag(title_tag, question_url):  # Skip tag which resolved failed
                            continue
                        title_sequence, title_img_list = resolve_tag(title_tag)

                        # Resolve analysis
                        analyze_tag = soup.select_one("div[class=paper-analyize-wrap]")
                        if not validate_tag(analyze_tag, question_url):  # Skip tag which resolved failed
                            continue
                        analyze_text = analyze_tag.text
                        analysis_sequence = {}
                        analysis_img_list = []
                        if utils.contains_str(analyze_text, '显示答案解析'):
                            print("Warning! You[%s] have not login! Answer is invisible! Try to refresh cookies..." % self.name)
                            # exit()
                            if self.refresh_cookies():
                                print("Thread[%s] refresh cookies success!" % self.name)
                            analysis_sequence[FETCHED] = False
                        elif utils.contains_str(analyze_text, '限制'):
                            if warn:
                                print("Sorry! Thread[%s] has run out of the accessing times for analysis!" % self.name)
                                warn = False
                            analysis_sequence[FETCHED] = False
                        else:
                            analysis_sequence, analysis_img_list = resolve_analysis(analyze_tag.contents[0])
                            analysis_sequence[FETCHED] = True

                        message_tag = soup.select_one("div[class=paper-message-attr]")
                        question_message = resolve_message(message_tag)

                        question_data = {ID: item[ID], TITLE: title_sequence}
                        question_data.update(question_message)
                        question_data.update(analysis_sequence)
                        question_list.append(question_data)

                        # 所有标签解析成功后才把图片存入数据库
                        # if len(title_img_list) != 0:
                        #     img_list += title_img_list
                        # if len(option_img_list) != 0:
                        #     img_list += option_img_list
                        if len(analysis_img_list) != 0:
                            img_list += analysis_img_list

                    except Exception as ex:  # 捕获所有异常，出错后单独处理，避免中断
                        print(ex)
                        print("Thread[%s] resolve failed id=[%s] url=[%s]" % (self.name, item[ID], question_url))
                    if len(question_list) == QUESTION_BATCH_SIZE:
                        save_questions(self.name, img_list, question_list, start_time, time.time())
                        start_time = time.time()
            if len(question_list) > 0:
                save_questions(self.name, img_list, question_list, start_time, time.time())
                print(self.name, img_list, question_list, start_time, time.time())
            break
        print("Thread[%s] finished resolving [%d] questions taken %.2fs"
              % (self.name, count, time.time() - begin_time))

    def resolve_computation(self, criteria):
        last = 0
        img_list = []
        question_list = []
        warn = True
        start_time = time.time()
        begin_time = start_time
        count = 0
        while count < self.max_size:
            offset = last + BATCH_SIZE * self.id
            url_list = db_client.load_unresolved_url(BATCH_SIZE, offset, criteria)
            print("Thread[%s] start to fetch [%d] questions" %(self.name, BATCH_SIZE))
            # url_list = ["http://www.51jiaoxi.com/question-328701.html"]
            # url_list = db_client.load_url_by_id(['328701'])
            # print(url_list)
            count += len(url_list)
            last += BATCH_SIZE * self.thread_nums
            if len(url_list) == 0:
                break
            for item in url_list:
                if not item[RESOLVED]:  # False indicates current url has not been resolved yet
                    try:
                        question_url = item['url']
                        resp = requests.get(url=question_url, headers=self.headers)
                        if resp.status_code != requests.codes.ok:
                            print("Resolved failed for url[%s] status_code[%d]" % (question_url, resp.status_code))
                            continue
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # Resolve title
                        title_tag = soup.select_one("div[class=paper-question-title]")
                        if not validate_tag(title_tag, question_url):  # Skip tag which resolved failed
                            continue
                        title_sequence, title_img_list = resolve_tag(title_tag)

                        # Resolve analysis
                        analyze_tag = soup.select_one("div[class=paper-analyize-wrap]")
                        if not validate_tag(analyze_tag, question_url):  # Skip tag which resolved failed
                            continue
                        analyze_text = analyze_tag.text
                        analysis_sequence = {}
                        analysis_img_list = []
                        if utils.contains_str(analyze_text, '显示答案解析'):
                            print("Warning! You[%s] have not login! Answer is invisible! Try to refresh cookies..." % self.name)
                            # exit()
                            if self.refresh_cookies():
                                print("Thread[%s] refresh cookies success!" % self.name)
                            analysis_sequence[FETCHED] = False
                        elif utils.contains_str(analyze_text, '限制'):
                            if warn:
                                print("Sorry! Thread[%s] has run out of the accessing times for analysis!" % self.name)
                                warn = False
                            analysis_sequence[FETCHED] = False
                        else:
                            analysis_sequence, analysis_img_list = resolve_analysis(analyze_tag.contents[0])
                            analysis_sequence[FETCHED] = True

                        message_tag = soup.select_one("div[class=paper-message-attr]")
                        question_message = resolve_message(message_tag)

                        question_data = {ID: item[ID], TITLE: title_sequence}
                        question_data.update(question_message)
                        question_data.update(analysis_sequence)
                        question_list.append(question_data)

                        # 所有标签解析成功后才把图片存入数据库
                        # if len(title_img_list) != 0:
                        #     img_list += title_img_list
                        # if len(option_img_list) != 0:
                        #     img_list += option_img_list
                        if len(analysis_img_list) != 0:
                            img_list += analysis_img_list

                    except Exception as ex:  # 捕获所有异常，出错后单独处理，避免中断
                        print(ex)
                        print("Thread[%s] resolve failed id=[%s] url=[%s]" % (self.name, item[ID], question_url))
                    if len(question_list) == QUESTION_BATCH_SIZE:
                        save_questions(self.name, img_list, question_list, start_time, time.time())
                        start_time = time.time()
            if len(question_list) > 0:
                save_questions(self.name, img_list, question_list, start_time, time.time())
                # print(self.name, img_list, question_list, start_time, time.time())
            break
        print("Thread[%s] finished resolving [%d] questions taken %.2fs"
              % (self.name, count, time.time() - begin_time))

    def resolve_synthesis(self, criteria):
        last = 0
        img_list = []
        question_list = []
        warn = True
        start_time = time.time()
        begin_time = start_time
        count = 0
        while count < self.max_size:
            offset = last + BATCH_SIZE * self.id
            url_list = db_client.load_unresolved_url(BATCH_SIZE, offset, criteria)
            print("Thread[%s] start to fetch [%d] questions" %(self.name, BATCH_SIZE))
            # url_list = ["http://www.51jiaoxi.com/question-692577.html"]
            # url_list = db_client.load_url_by_id(['692577'])
            # print(url_list)
            count += len(url_list)
            last += BATCH_SIZE * self.thread_nums
            if len(url_list) == 0:
                break
            for item in url_list:
                if not item[RESOLVED]:  # False indicates current url has not been resolved yet
                    try:
                        question_url = item['url']
                        resp = requests.get(url=question_url, headers=self.headers)
                        if resp.status_code != requests.codes.ok:
                            print("Resolved failed for url[%s] status_code[%d]" % (question_url, resp.status_code))
                            continue
                        # print(resp)
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # Resolve title
                        title_tag = soup.select_one("div[class=paper-question-title]")
                        if not validate_tag(title_tag, question_url):  # Skip tag which resolved failed
                            continue
                        title_sequence, title_img_list = resolve_tag(title_tag)

                        # Resolve sub_title
                        subtitle_tag = soup.select_one("ol[class=paper-subquestion]")
                        if not validate_tag(subtitle_tag, question_url):  # Skip tag which resolved failed
                            continue
                        subtitle_sequence, subtitle_img_list = resolve_sub_question(subtitle_tag)
                        # print(subtitle_sequence)
                        # Resolve analysis
                        analyze_tag = soup.select_one("div[class=paper-analyize-wrap]")
                        if not validate_tag(analyze_tag, question_url):  # Skip tag which resolved failed
                            continue
                        analyze_text = analyze_tag.text
                        analysis_sequence = {}
                        analysis_img_list = []
                        if utils.contains_str(analyze_text, '显示答案解析'):
                            print("Warning! You[%s] have not login! Answer is invisible! Try to refresh cookies..." % self.name)
                            # exit()
                            if self.refresh_cookies():
                                print("Thread[%s] refresh cookies success!" % self.name)
                            analysis_sequence[FETCHED] = False
                        elif utils.contains_str(analyze_text, '限制'):
                            if warn:
                                print("Sorry! Thread[%s] has run out of the accessing times for analysis!" % self.name)
                                warn = False
                            analysis_sequence[FETCHED] = False
                        else:
                            analysis_sequence, analysis_img_list = resolve_analysis(analyze_tag.contents[0])
                            if len(subtitle_sequence) > 0:
                                subtitle_answer_squence, subtitle_answer_img_list = resolve_sub_analysis(subtitle_tag)
                                # print(subtitle_answer_squence)
                                analysis_sequence.update(subtitle_answer_squence)
                            analysis_sequence[FETCHED] = True

                        message_tag = soup.select_one("div[class=paper-message-attr]")
                        question_message = resolve_message(message_tag)

                        question_data = {ID: item[ID], TITLE: title_sequence,SUBTITLE:subtitle_sequence}
                        question_data.update(question_message)
                        question_data.update(analysis_sequence)
                        question_list.append(question_data)

                        # 所有标签解析成功后才把图片存入数据库
                        # if len(title_img_list) != 0:
                        #     img_list += title_img_list
                        # if len(option_img_list) != 0:
                        #     img_list += option_img_list
                        if len(analysis_img_list) != 0:
                            img_list += analysis_img_list

                    except Exception as ex:  # 捕获所有异常，出错后单独处理，避免中断
                        print(ex)
                        print("Thread[%s] resolve failed id=[%s] url=[%s]" % (self.name, item[ID], question_url))
                    if len(question_list) == QUESTION_BATCH_SIZE:
                        save_questions(self.name, img_list, question_list, start_time, time.time())
                        start_time = time.time()
            if len(question_list) > 0:
                save_questions(self.name, img_list, question_list, start_time, time.time())
                # print(self.name, img_list, question_list, start_time, time.time())
            break
        print("Thread[%s] finished resolving [%d] questions taken %.2fs"
              % (self.name, count, time.time() - begin_time))
    
if __name__ == '__main__':
    options = Options()
    options.headless = True
    driver = webdriver.PhantomJS(executable_path="D:\\Tools\\ChromeDriver\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe")
    driver.get("https://www.baidu.com/")
    time.sleep(1)
    print(driver.current_url)
