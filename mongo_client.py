from pymongo import MongoClient
from pymongo.errors import *

from config import *


def insert_one(collection_name='', doc={}):
    try:
        with MongoClient(MONGO_HOST, MONGO_PORT) as client:
            db = client['math_questions']
            collection = db[collection_name]
            collection.insert_one(doc)
            return True
    except DuplicateKeyError as e:
        # print(e.details)
        return False


def insert_many(collection_name='', docs=[]):
    try:
        with MongoClient(MONGO_HOST, MONGO_PORT) as client:
            db = client['math_questions']
            collection = db[collection_name]
            collection.insert_many(docs)
            return True
    except BulkWriteError as e:
        # print(e.details)
        return False


# Load $num urls from the start item
def load_unresolved_url(num=0, start=0, filter={}):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client['math_questions']
        collection = db[COLLECTION_URL]
        filter["resolved"] = False
        docs = collection.find(filter, {"url": 1, "type": 1, 'resolved': 1}).skip(start).limit(num)
        data = []
        for doc in docs:
            data.append(doc)
        return data


def insert_or_update_cookies(cookies=[]):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client['math_questions']
        collection = db['cookie']
        for cookie in cookies:
            filter = {'name': cookie['name']}
            collection.update(spec=filter, document=cookie, upsert=True)


def load_cookies():
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client['math_questions']
        collection = db['cookie']
        docs = collection.find({})
        cookies = []
        for doc in docs:
            cookies.append(doc)
        return cookies

#load img urls
# def load_unresolved_imgs(collection_name='', num=0, start=0, filter={}):
#     collection = db[collection_name]
#     filter["resolved"] = False
#     imgs = collection.find(filter).skip(start).limit(num)
#     data = []
#     for img in imgs:
#         data.append(img)
#     return data

#update data
# def update_datas(collection_name='', num=0, start=0, filter = {}, string = ""):
#     collection = db[collection_name]
#     collection.update(filter,{"$set":{PLAIN_TEXT: string}})

# data = load_unresolved_imgs("img_url", 10, 0)
# print(data)
