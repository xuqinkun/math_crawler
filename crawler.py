import sys
import json
import mongo_client
from config import *
from crawler_task import Task


if __name__ == '__main__':
    """
        每个线程使用一个账户进行查询
    """
    usage = "USAGE:python crawler.py PHANTOMJS_PATH"
    ''' if len(sys.argv) != 2:
        #print(len(sys.argv))
        print(usage)
        print(sys.argv[0])
        exit(1) '''
    phantomjs_path =r'C:\Users\74765\Desktop\phantomjs-2.1.1-windows\bin\phantomjs.exe' #sys.argv[0]
    #accounts = mongo_client.get_accounts()
    with open(r'keys\accounts.json','r',encoding='utf-8') as f:
        accounts=json.load(f)
    #criteria = {"class.class1": {"$nin": ["图形的性质", "图形的变换"]}, "type": SINGLE_CHOICE}
    criteria = {"type": SINGLE_CHOICE}
    if ANALYSIS_ONLY:
        count=mongo_client.get_fetched_false_count(criteria)
    else:
        count = mongo_client.get_unresolved_url_count(criteria)
    
    thread_nums = len(accounts)
    batch_size = int(count / thread_nums) + len(accounts)
    # Exclude: $nin, include: $in
    id = 0
    #for account in accounts:
    t = Task(id, thread_nums, SINGLE_CHOICE, criteria, accounts[2], False, batch_size, phantomjs_path,ANALYSIS_ONLY)
    t.start()
    id += 1