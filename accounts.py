from config import *
import utils
import mongo_client
import json
#账号文件
path=r'accounts.json'

if __name__ == "__main__":
    f=open(path,'r')
    accounts_list=json.load(f)

    for i in accounts_list:
        #加密
        phone=utils.rsa_encrypt(i['phone'])
        pwd=utils.rsa_encrypt(i['password'])

        account={'phone':phone,'password':pwd}
        #print(account)
        mongo_client.insert_one('account',account)
    #print('insert finish')
    
    id_list=mongo_client.get_accounts()
    
    #print(id_list)