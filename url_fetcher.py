from selenium import webdriver
import mongo_client
import time
from threading import Thread

COLLECTION = 'question_url'
BATCH_SIZE = 1000


def next_page(driver):
    try:
        driver.find_element_by_css_selector('li[class="btn-next"]').click()
        time.sleep(0.5)
        return True
    except:
        return False


# Index page of math questions
# Each thread takes one task
def fetch_question_list(url='', task_id=0):
    thread_name = "Thread-%s" % task_id
    print("%s fetch question urls from %s..." % (thread_name, url))
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)
    driver.maximize_window()
    # Click navigate item
    ul = driver.find_element_by_css_selector("ul[class='manual-main-right-top-list']")
    ul.find_elements_by_tag_name('li')[task_id + 1].click()
    time.sleep(1)
    questions = []
    start_time = time.time()
    begin_time = start_time
    count = 0
    while True:
        question_items = driver.find_elements_by_class_name('manual-main-right-item')
        for item in question_items:
            question_id = item.find_element_by_class_name("manual-question").get_attribute('id').split('_')[-1]
            question_type = item.find_element_by_class_name("manual-message-span1").text
            question_url = item.find_elements_by_class_name("manual-message-handle a")[1].get_attribute("href")
            data = {"id": question_id, "type": question_type, "url": question_url, "resolved": False}
            questions.append(data)
        if not next_page(driver):
            break
        # When questions's size reaches to _batch_size, insert into mongo:
        size = len(questions)
        if size == BATCH_SIZE:
            if not mongo_client.insert_many(COLLECTION, questions):
                print('Batch insertion failed, try insert one by one!')
                for item in questions:
                    mongo_client.insert_one(COLLECTION, item)
            questions.clear()
            end_time = time.time()
            print("%s fetched %d urls takes %.2fs" % (thread_name, size, end_time - start_time))
            start_time = end_time
        count += 1
    print("%s finished fetching %d questions taken %2.fs" % (thread_name, count, begin_time - time.time()))
    driver.quit()


def dispatch_task(url=''):
    #print("Fetch question urls from %s..." % url)
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)
    driver.maximize_window()
    # Click navigate item
    ul = driver.find_element_by_css_selector("ul[class='manual-main-right-top-list']")
    size = len(ul.find_elements_by_tag_name('li')) - 1
    driver.quit()
    for index in range(0, size):
        Thread(target=fetch_question_list, args=(index_url, index)).start()



index_url = 'http://zujuan.51jiaoxi.com/#/paperFrontend/manual?stage_id=2&subject_id=3'
dispatch_task(index_url)
