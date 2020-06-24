import sys
import json
import mongo_client
from config import *
from crawler_task import Task



def str2bool(s):
    return s in ["true", "True", "TRUE"]


def str2type(s="0"):
    if s == '0':
        return SINGLE_CHOICE
    elif s == "1":
        return "填空题"
    elif s == "2":
        return "计算题"
    elif s == "3":
        return "综合题"
    return None


if __name__ == '__main__':
    """
        每个线程使用一个账户进行查询
    """
    usage = """USAGE:python crawler.py PHANTOMJS_PATH QUESTION_TYPE [ANALYSIS_ONLY(True/False)]
       [QUESTION_TYPE]
        0: 单选题
        1: 填空题
        2: 计算题
        3：综合题
        """
    if len(sys.argv) < 3:
        print(usage)
        exit(1)
    phantomjs_path = sys.argv[1]
    question_type = str2type(sys.argv[2])
    if question_type is None:
        print("Bad question type.\n%s" % usage)
        exit(1)
    analysis_only = False
    if len(sys.argv) > 3:
        analysis_only = str2bool(sys.argv[3])
    print(analysis_only)
    accounts = mongo_client.get_accounts()
    print(accounts)
    criteria = {"class.class1": {"$nin": ["图形的性质", "图形的变换"]}, "type": question_type}
    if analysis_only:
        print("Only fetch analysis for (%s)" % question_type)
        count = mongo_client.get_fetched_false_count(criteria)
    else:
        count = mongo_client.get_unresolved_url_count(criteria)
    
    thread_nums = len(accounts)
    if thread_nums == 0:
        print("Please insert accounts first!")
        exit(0)
    batch_size = int(count / thread_nums) + thread_nums
    # Exclude: $nin, include: $in
    thread_id = 0
    for account in accounts:
        print("getting into thread")
        t = Task(thread_id, thread_nums, question_type, criteria, account,
                 False, batch_size, phantomjs_path, analysis_only)
        t.start()
        thread_id += 1
        # break
