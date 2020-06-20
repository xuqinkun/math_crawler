import requests
import time
from bs4.element import *
import mongo_client
from config import *
from math_resolve import *
from selenium import webdriver
import selenium.webdriver.common.action_chains as ac


# Convert the img src to MathML
def resolve_mathml(src=''):
    url_decode = parse.unquote(src)
    return re.findall("<math.*math>", url_decode)[0]


# Get uuid from the img src
def get_uuid(src=''):
    name = src.split('/')[-1]
    return name.split('.')[0]


# Resolve the tag as a plain text
# HTML Tag is a tree, use DFS to traverse
def resolve_title(tag=Tag(name='')):
    plain_text = []
    url_map = []
    for child in tag.children:  # Traverse the children of tag
        if isinstance(child, NavigableString):  # NavigableString is a plain text, just append to plain_text
            plain_text.append({PLAIN_TEXT: str(child)})
        elif child.name == 'br':  # Tag <br>, append a new line
            pass
        elif child.name == 'img':  # Tag <img>, append the attribute 'src'
            src = str(child['src'])
            if src.find('MathMLToImage') != -1:  # URL contains MathML then just resolve it
                plain_text.append({LATEX: mathml2latex(resolve_mathml(src))})
            elif src.find(PNG) != -1:  # Simple url for png
                key = get_uuid(src)
                plain_text.append({PNG: key})  # Placeholder for OCR to find the image path
                url_map.append({key: src})
            text, temp_map = resolve_title(child)  # Call resolve_tag recursively
            plain_text += text
            url_map += temp_map
        elif isinstance(child, Tag):  # If current child is a tag, call resolve_tag recursively
            text, temp_map = resolve_title(child)
            plain_text += text
            url_map += temp_map
    return plain_text, url_map


# Resolve the tag as a plain text
# HTML Tag is a tree, use DFS to travers
def resolve_options(tag=Tag(name='')):
    options = []
    src_map = []
    for div in tag.contents[0].contents:
        key = str(div.contents[0].text).strip(' ').rstrip('.')
        value_tag = div.contents[1].contents[0]
        value = {}
        if isinstance(value_tag, NavigableString):
            value = {PLAIN_TEXT: str(value_tag).strip(' ')}
        elif isinstance(value_tag, Tag):
            src = value_tag['src']
            if src.find(PNG) != -1:
                uuid = get_uuid(src)
                value = {PNG: uuid}
                src_map.append({uuid: src})
            elif src.find('MathMLToImage') != -1:
                value = {LATEX: mathml2latex(resolve_mathml(src))}
        options.append({key: value})
    return options, src_map


# 单选题解析
def resolve_single():
    last = 0
    while True:
        data = mongo_client.load_unresolved_url(BATCH_SIZE, last, {"type": "单选题"})
        if len(data) == 0:
            break
        last += BATCH_SIZE
        for item in data:
            if not item['resolved']:  # False indicates current url has not been resolved yet
                resp = requests.get(url=item['url'], headers=HEADERS)
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.select_one("div .paper-question-title")
                title_sequence, title_src_list = resolve_title(title)
                print("**Title**", title_sequence, title_src_list)
                options_tag = soup.select_one("div .paper-question-options")
                option_sequence, option_src_list = resolve_options(options_tag)
                print("**Options**", option_sequence, option_src_list)
                analyze = soup.select_one("div .paper-analyize-wrap")
                if analyze.text == '显示答案解析':
                    print("Login failure!Please refresh cookies!")
                    break


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


def get_cookies(use_phantomjs=False, params={}):
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
    cookies = mongo_client.load_cookies()
    if is_valid_cookies(cookies):
        return cookies
    login_url = r'http://www.51jiaoxi.com/login'
    if use_phantomjs:
        driver = webdriver.PhantomJS()
        driver.get(login_url)
        time.sleep(3)
        ac.actionChains(driver).click(driver.find_element_by_css_selector('div.phone.login-way.wechat-leave')).perform()
        time.sleep(3)
        ac.ActionChains(driver).send_keys_to_element(driver.find_element_by_id('login-auth-phone'),
                                                     params['phone']).perform()
        time.sleep(1)
        ac.ActionChains(driver).send_keys_to_element(driver.find_element_by_id('login-auth-password'),
                                                     params['password']).perform()
        time.sleep(1)
        ac.ActionChains(driver).click(driver.find_element_by_css_selector('button.login-button.jx-button')).perform()
        time.sleep(3)
        error_msg = driver.find_element_by_css_selector("span[class='alert-message error']").text
        if error_msg != '':
            print(error_msg)
            exit(1)
    else:
        driver = webdriver.Chrome()
        driver.get(login_url)
        print("Please scan two-dimension code to login! And press any key to continue!")
        input()
    cookies = driver.get_cookies()
    mongo_client.insert_or_update_cookies(cookies)
    return cookies


def refresh_cookies(login_with_wechat=False, use_phantomjs=True):
    cookies = get_cookies(login_with_wechat, use_phantomjs)
    cookies_str = ''
    for cookie in cookies:
        cookies_str += str(cookie['name']) + '=' + str(cookie['value']) + ';'
    HEADERS[COOKIE] = cookies_str


if __name__ == '__main__':
    refresh_cookies(True)
    resolve_single()
