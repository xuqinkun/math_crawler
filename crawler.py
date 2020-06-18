import requests
import time
from bs4.element import *

import mongo_client
from config import *
from math_resolve import *
from selenium import webdriver


# Convert the img src to MathML
def resolve_mathml(src=''):
    url_decode = parse.unquote(src)
    return re.findall("<math.*math>", url_decode)[0]


# Get uuid from the img src
def get_uuid(src=''):
    name = src.split('/')[-1]
    return name.split('.')[0]


# Resolve the tag as a plain text
# HTML Tag is a tree, use DFS to travers
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
        data = mongo_client.load_unresolved_url(COLLECTION_URL, BATCH_SIZE, last, {"type": "单选题"})
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


def get_cookies(login_with_wechat=False):
    """
        get cookies after logining in 51jiaoxi and return cookies as a string.
        you should login in this site mannually so this function will wait for pressing a key after you login in this site.
        WARNING: you should download chromedriver and move this application to the current floder.
        If you don't have this application, you can access https://chromedriver.chromium.org/,
        check your chrome version and download corresponding version's chromedriver.
    """
    # with webdriver.Chrome(executable_path=r'./chromedriver') as driver:
    with webdriver.Chrome() as driver:
        driver.get(login_url)
        # waiting for logining in this site and press any key to continue
        if login_with_wechat:
            print("Please scan  two-dimension code to login! And press any key to continue!")
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
        cookies_str = ''
        for cookie in cookies:
            cookies_str += str(cookie['name']) + '=' + str(cookie['value']) + ';'
        return cookies_str


# Update cookie
def login(login_with_wechat=False):
    cookies = get_cookies(login_with_wechat)
    HEADERS[COOKIE] = cookies


if __name__ == '__main__':
    login(False)
    resolve_single()
