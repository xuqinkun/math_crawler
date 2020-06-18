import time
import mongo_client

from threading import Thread
from selenium import webdriver
from constant import *


def next_page(driver):
    try:
        driver.find_element_by_css_selector('li[class="btn-next"]').click()
        time.sleep(0.5)
        return True
    except:
        return False


def travers_pages(driver, thread_name='', _class=''):
    questions = []
    count = 0
    start_time = time.time()
    i = 0
    while i < 100:  # 超出一百次退出
        i += 1
        question_items = driver.find_elements_by_class_name('manual-main-right-item')
        for item in question_items:
            question_id = item.find_element_by_class_name("manual-question").get_attribute('id').split('_')[-1]
            question_type = item.find_element_by_class_name("manual-message-span1").text
            question_url = item.find_elements_by_class_name("manual-message-handle a")[1].get_attribute("href")
            data = {"id": question_id, "type": question_type, "url": question_url, "resolved": False, "class": _class}
            questions.append(data)
        if not next_page(driver):
            break
        # When questions's size reaches to _batch_size, insert into mongo:
        size = len(questions)
        if size == BATCH_SIZE:
            insert_many(questions)
            questions.clear()
            print("%s fetched %d urls takes %.2fs" % (thread_name, size, time.time() - start_time))
            start_time = time.time()
        count += 1
    if len(questions) != 0:
        insert_many(questions)
    return count


def insert_many(questions):
    if not mongo_client.insert_many(COLLECTION_URL, questions):
        print('==========Batch insertion failed, try insert one by one!==========')
        count = 0
        for item in questions:
            if mongo_client.insert_one(COLLECTION_URL, item):
                count += 1
        print('==========Inserted %d items total one by one!==========' % count)


# Index page of math questions
# Each thread takes one task
def fetch_question_list(url='', task_id=0):
    thread_name = "Thread-%s" % task_id
    print("%s fetch question urls from %s..." % (thread_name, url))
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)
    driver.maximize_window()
    time.sleep(0.5)
    # 点击'按知识点选题'
    driver.find_elements_by_css_selector("div.manual-main-left-top span")[2].click()
    start_time = time.time()

    count = 0
    # 遍历左侧导航栏
    for level1 in driver.find_elements_by_css_selector("li[class='folder level-1']"):
        level1.click()
        time.sleep(0.5)
        class1 = level1.find_element_by_css_selector("div .li-slot").text
        for level2 in level1.find_elements_by_css_selector("li[class='folder level-2']"):
            level2.click()
            time.sleep(0.5)
            class2 = level2.find_element_by_css_selector("div .li-slot").text
            for level3 in level2.find_elements_by_css_selector("li[class='file level-3']"):
                level3.click()
                time.sleep(0.5)
                class3 = level3.find_element_by_css_selector("div .li-slot").text
                _class = {"class1": class1, "class2": class2, "class3": class3}
                # 点击题型，每个线程负责一种题型
                ul = driver.find_element_by_css_selector("ul[class='manual-main-right-top-list']")
                ul.find_elements_by_tag_name('li')[task_id + 1].click()
                time.sleep(0.5)
                count += travers_pages(driver, thread_name, _class)
    print("%s finished fetching %d questions taken %2.fs" % (thread_name, count, time.time() - start_time))
    driver.quit()


def dispatch_task(url=''):
    # print("Fetch question urls from %s..." % url)
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)
    driver.maximize_window()
    # Click navigate item
    ul = driver.find_element_by_css_selector("ul[class='manual-main-right-top-list']")
    size = len(ul.find_elements_by_tag_name('li')) - 1
    driver.quit()
    for index in range(0, size):
        Thread(target=fetch_question_list, args=(url, index)).start()


index_url = 'http://zujuan.51jiaoxi.com/#/paperFrontend/manual?stage_id=2&subject_id=3'
dispatch_task(index_url)
