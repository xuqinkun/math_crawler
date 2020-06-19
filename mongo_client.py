from pymongo import MongoClient
from pymongo.errors import *

client = MongoClient('121.48.165.7', 11118)
db = client['math_questions']


def insert_one(collection_name='', doc={}):
    try:
        collection = db[collection_name]
        collection.insert_one(doc)
        return True
    except DuplicateKeyError as e:
        # print(e.details)
        return False


def insert_many(collection_name='', docs=[]):
    try:
        collection = db[collection_name]
        collection.insert_many(docs)
        return True
    except BulkWriteError as e:
        # print(e.details)
        return False


# Load $num urls from the start item
def load_unresolved_url(collection_name='', num=0, start=0, filter={}):
    collection = db[collection_name]
    filter["resolved"] = False
    docs = collection.find(filter, {"url": 1, "type": 1, 'resolved': 1}).skip(start).limit(num)
    data = []
    for doc in docs:
        data.append(doc)
    return data

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
