import json

from mongo_client import MongoDriver
import utils
from config import *

# 账号文件
path = r'keys/accounts.json'


def insert_accounts(mongo_host, mongo_port):
    f = open(path, 'r')
    accounts_list = json.load(f)
    accounts = []
    for account in accounts_list:
        # 加密
        phone = account['phone']
        pwd = utils.rsa_encrypt(account['password'])
        accounts.append({'phone': phone, 'password': pwd})
    mongo_client = MongoDriver(mongo_host, mongo_port)
    mongo_client.insert_many(ACCOUNT, accounts)
if __name__ == "__main__":
    insert_accounts('121.48.165.6',11118)
