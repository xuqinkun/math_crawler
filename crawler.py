import sys

import mongo_client
from config import *
from crawler_task import Task


if __name__ == '__main__':
    """
        每个线程使用一个账户进行查询
    """
    usage = "USAGE:python crawler.py PHANTOMJS_PATH"
    if len(sys.argv) != 2:
        print(usage)
        exit(1)
    phantomjs_path = sys.argv[1]
    accounts = mongo_client.get_accounts()
    criteria = {"class.class1": {"$nin": ["图形的性质", "图形的变换"]}, "type": SINGLE_CHOICE}
    count = mongo_client.get_unresolved_url_count(criteria)
    thread_nums = len(accounts)
    batch_size = int(count / thread_nums) + len(accounts)
    # Exclude: $nin, include: $in
    id = 0
    for account in accounts:
        t = Task(id, thread_nums, SINGLE_CHOICE, criteria, account, False, batch_size, phantomjs_path)
        t.start()
        id += 1
