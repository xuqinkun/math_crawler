from pymongo import MongoClient
from pymongo.errors import *
import utils
from config import *



def contains(pngs=[], target=[]):
    for png in pngs:
        try:
            if target.index(png):
                return True
        except ValueError:
            continue
    return False


class MongoDriver:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def insert_one(self, collection_name='', doc={}):
        if len(doc) == 0:
            return True
        try:
            with MongoClient(self.host, self.port) as client:
                db = client[DB]
                collection = db[collection_name]
                collection.insert_one(doc)
                return True
        except DuplicateKeyError as e:
            print(e.details)
            return False
        except Exception as e:
            print(e)
            return False

    def insert_many(self, collection_name='', docs=[]):
        if len(docs) == 0:
            return True
        try:
            with MongoClient(self.host, self.port) as client:
                db = client[DB]
                collection = db[collection_name]
                collection.insert_many(docs)
                return True
        except BulkWriteError as e:
            print(e.details)
            return False
        except Exception as e:
            print(e)
            return False

    def update_one(self,collection_name='',doc={}):
        if len(doc) == 0:
            return True
        try:
            with MongoClient(self.host, self.port) as client:
                db = client[DB]
                collection = db[collection_name]
                filter_=doc['filter']
                update_=doc['update']
                collection.update_one(filter=filter_,update=update_)
                return True
        except Exception as e:
            print(e)
            return False


    # Load $num urls from the start item
    def find(self, collection_name='', num=0, start=0, criteria={}):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[collection_name]
            docs = collection.find(criteria).skip(start).limit(num)
            data = []
            for doc in docs:
                data.append(doc)
            return data

    def find_url_by_ids(self, ids=[]):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_URL]
            docs = collection.find({ID: {"$in": ids}})
            data = []
            for doc in docs:
                data.append(doc)
            return data

    # Load $num urls from the start item
    def load_unresolved_url(self, num=0, start=0, criteria={}):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_URL]
            criteria[RESOLVED] = False
            docs = collection.find(criteria).skip(start).limit(num)
            data = []
            for doc in docs:
                data.append(doc)
            return data

    def load_url_by_id(self, ids=[]):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_URL]
            criteria = {"id": {"$in": ids}}
            docs = collection.find(criteria)
            data = []
            for doc in docs:
                data.append(doc)
            return data

    def load_unchecked_img(self,num=10,start=0):
        with MongoClient(self.host, self.port) as client:
            db=client[DB]
            collection=db[COLLECTION_IMAGE]
            filter_={'checked':False,'checking':False}
            update_={"$set":{"checking":True}}
            data=[]
            for i in range(num):
                d=collection.find_one_and_update(filter=filter_,update=update_)
                data.append(d)
            return data

    def insert_or_update_cookies(self, cookies=[]):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COOKIE]
            filter = {PHONE: cookies[PHONE]}
            collection.update(spec=filter, document=cookies, upsert=True)


    def load_cookies(self, phone_number=""):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COOKIE]
            cookies = {}
            for doc in collection.find({ACCOUNT: phone_number}):
                cookies = doc
            return cookies

    def update_url_resolved(self, img_id_list=[]):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_URL]
            for id in img_id_list:
                collection.update_one(filter={"id": id}, update={"$set": {RESOLVED: True}})
        return True

    def update_img_info(self, img_text_list={}):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_IMAGE]
            count = 0
            for uuid, text in img_text_list.items():
                # print(uuid,text)
                if text != "":
                    if text in ['A','B','C','D']:
                        print(uuid,text)
                        collection.update_one(filter={UUID: uuid,CHECKED:False,CHECKING:False}, update={"$set": {RESOLVED: True, PLAIN_TEXT: text, CHECKED:True}})
                    else:
                        collection.update_one(filter={UUID: uuid,CHECKED:False,CHECKING:False}, update={"$set": {RESOLVED: True, PLAIN_TEXT: text}})
                    count = count + 1
            print("%d images text updated "% count)
        return True

    def update_img_check_info(self,data={}):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_IMAGE]
            filter_={'_id':data['_id']}
            update={'$set':{'resolved':data['resolved'],'checked':data['checked'],'plain_text':data['plain_text'],'checking':data['checking']}}
            try:
                collection.update_one(filter=filter_,update=update)
                return True
            except Exception as e:
                print(e)
                return False

    def update_analysis(self, analysis_data={}):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_DETAILS]
            question_id = analysis_data[ID]
            analysis_data.pop(ID)
            collection.update_one(filter={"id": question_id}, update={"$set": analysis_data})

    def update_url_fake(self, url_id):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_URL]
            collection.update_one(filter={"id": url_id}, update={"$set": {FAKE: True}})

    def resolve_png_keys(self, docs):
        png_list = []
        if isinstance(docs, list):
            for doc in docs:
                png_list += self.resolve_png_keys(doc)
        else:
            for key in docs.keys():
                value = docs[key]
                if key == COLLECTION_IMAGE:
                    png_list.append(value)
                elif isinstance(value, list) or isinstance(value, dict):
                    png_list += self.resolve_png_keys(value)
        return png_list

    def get_png_list(self, target=[]):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_DETAILS]
            docs = collection.find({})
            png_list = []
            for doc in docs:
                uuids = self.resolve_png_keys(doc)
                if contains(uuids, target):
                    png_list.append(doc["id"])
            return png_list


    def load_img_src(self,batch_size = 100):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_IMAGE]
            docs = collection.find({})
            png_dict = {}
            count = 0
            for doc in docs:
                # print(doc)
                if not doc[RESOLVED] and not doc[CHECKING] and not doc[CHECKED]:
                    png_dict[doc[UUID]] = doc["src"]
                    count += 1
                if count >= batch_size:
                    break
            return png_dict


    # def get_unresolved_url_count():
    #     with MongoClient(MONGO_HOST, MONGO_PORT) as client:
    #         db = client[DB]
    #         collection = db[QUESTION_URL]
    #         return collection.count({RESOLVED: False})

    def get_unresolved_url_count(self, criteria):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_URL]
            criteria[RESOLVED] = False
            return collection.count(criteria)

    def get_fetched_false_count(self, criteria):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_DETAILS]
            criteria[FETCHED] = False
            return collection.count(criteria)

    def get_accounts(self):
        """
        From mongodb get id and password data
        :return:
        """
        account_list = []
        with MongoClient(self.host, self.port) as client:
            collection = client.math_questions.account
            cursor = collection.find()
            for account in cursor:
                phone = account['phone']
                pwd = utils.rsa_decrypt(account['password'])
                account_list.append({'phone': phone, 'password': pwd})
        return account_list

    def get_img_of_options(self):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_DETAILS]
            docs = collection.find({})
            uuids = []
            for doc in docs:
                option = doc[OPTIONS]
                for values in option.values():
                    for value in values:
                        for key in value.keys():
                            if key != MATH_ML and key != PLAIN_TEXT:
                                uuids.append(value[key])
            return uuids

    def get_img_of_title(self):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[QUESTION_DETAILS]
            docs = collection.find({})
            uuids = []
            for doc in docs:
                title = doc[TITLE]
                for item in title:
                    for key in item.keys():
                        if key != MATH_ML and key != PLAIN_TEXT:
                            uuids.append(item[key])
            return uuids

    def remove_img(self, uuid_list):
        with MongoClient(self.host, self.port) as client:
            db = client[DB]
            collection = db[COLLECTION_IMAGE]
            ret = collection.delete_many({UUID: {"$in": uuid_list}})
            print(ret.deleted_count)


if __name__ == '__main__':
    client = MongoClient("localhost", 27017)
    img_list1 = client.get_img_of_title()
    img_list2 = client.get_img_of_options()
