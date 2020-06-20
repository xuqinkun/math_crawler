import json

import mongo_client
import utils
from config import *

# 账号文件
path = r'keys/accounts.json'


def insert_accounts():
    f = open(path, 'r')
    accounts_list = json.load(f)
    accounts = []
    for account in accounts_list:
        # 加密
        phone = account['phone']
        pwd = utils.rsa_encrypt(account['password'])
        accounts.append({'phone': phone, 'password': pwd})
    mongo_client.insert_many(ACCOUNT, accounts)


if __name__ == "__main__":
    # insert_accounts()
    id_list = mongo_client.get_accounts()
    print(id_list)
