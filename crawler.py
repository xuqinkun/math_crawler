import argparse

from crawler_task import Task
from mongo_client import MongoDriver


def str2bool(s):
    return s in ["true", "True", "TRUE"]


def str2type(s="0"):
    if s == 0:
        return "单选题"
    elif s == 1:
        return "填空题"
    elif s == 2:
        return "计算题"
    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip',
                        dest='ip',
                        type=str,
                        required=True,
                        help='the ip of host')
    parser.add_argument('-p', '--port',
                        dest='port',
                        type=int,
                        required=True,
                        help='the port of db')
    parser.add_argument('--driver-path',
                        dest='driver_path',
                        type=str,
                        required=True,
                        help='the path to the PhantomJS')
    parser.add_argument('-q', '--question_type',
                        dest='question_type',
                        type=int,
                        required=True,
                        choices=[0, 1, 2],
                        help='the question type you want to get.\n[QUESTION_TYPE]\n0: 单选题\n1: 填空题\n2: 计算题')
    parser.add_argument('-a', '--analysis_only',
                        dest='analysis_only',
                        type=bool,
                        default=False,
                        help='if true, this script will only get analysis only')
    return parser.parse_args()


if __name__ == '__main__':
    """
        每个线程使用一个账户进行查询
    """
    usage = """USAGE:python crawler.py PHANTOMJS_PATH QUESTION_TYPE [ANALYSIS_ONLY(True/False)]
       [QUESTION_TYPE]
        0: 单选题
        1: 填空题
        2: 计算题
        """
    option = parse_args()
    phantomjs_path = option.driver_path
    question_type = str2type(option.question_type)
    analysis_only = option.analysis_only

    mongo_client = MongoDriver(option.ip, option.port)
    accounts = mongo_client.get_accounts()
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
        t = Task(thread_id, thread_nums, question_type, criteria, account,
                 False, batch_size, phantomjs_path, analysis_only, mongo_client)
        t.start()
        thread_id += 1
