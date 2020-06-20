from pymongo import MongoClient
from pymongo.errors import *

from config import *

IMAGE = 'image'

QUESTION_DETAILS = "question_details"

QUESTION_URL = 'question_url'


def insert_one(collection_name='', doc={}):
    if len(doc) == 0:
        return True
    try:
        with MongoClient(MONGO_HOST, MONGO_PORT) as client:
            db = client[DB]
            collection = db[collection_name]
            collection.insert_one(doc)
            return True
    except DuplicateKeyError as e:
        # print(e.details)
        return False


def insert_many(collection_name='', docs=[]):
    if len(docs) == 0:
        return True
    try:
        with MongoClient(MONGO_HOST, MONGO_PORT) as client:
            db = client[DB]
            collection = db[collection_name]
            collection.insert_many(docs)
            return True
    except BulkWriteError as e:
        # print(e.details)
        return False


# Load $num urls from the start item
def load_unresolved_url(num=0, start=0, criteria={}):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COLLECTION_URL]
        criteria["resolved"] = False
        docs = collection.find(criteria).skip(start).limit(num)
        data = []
        for doc in docs:
            data.append(doc)
        return data


def load_url_by_id(ids=[]):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COLLECTION_URL]
        criteria = {"id": {"$in": ids}}
        docs = collection.find(criteria)
        data = []
        for doc in docs:
            data.append(doc)
        return data


def insert_or_update_cookies(cookies=[]):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COOKIE]
        filter = {ACCOUNT: cookies[ACCOUNT]}
        collection.update(spec=filter, document=cookies, upsert=True)


def load_cookies(account=""):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COOKIE]
        return collection.find({ACCOUNT: account})[0][COOKIES]


def update_url_resolved(img_id_list=[]):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[QUESTION_URL]
        for id in img_id_list:
            collection.update_one(filter={"id": id}, update={"$set": {RESOLVED: True}})
    return True


def resolve_png_keys(docs):
    png_list = []
    if isinstance(docs, list):
        for doc in docs:
            png_list += resolve_png_keys(doc)
    else:
        for key in docs.keys():
            value = docs[key]
            if key == IMAGE:
                png_list.append(value)
            elif isinstance(value, list) or isinstance(value, dict):
                png_list += resolve_png_keys(value)
    return png_list


def contains(pngs=[], target=[]):
    for png in pngs:
        try:
            if target.index(png):
                return True
        except ValueError:
            continue
    return False


def get_png_list(target=[]):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[QUESTION_DETAILS]
        docs = collection.find({})
        png_list = []
        for doc in docs:
            uuids = resolve_png_keys(doc)
            if contains(uuids, target):
                png_list.append(doc["id"])
        return png_list


def load_img_src():
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[IMAGE]
        docs = collection.find({})
        png_list = []
        for doc in docs:
            png_list.append(doc[UUID])
        return png_list


if __name__ == '__main__':
    # data = load_unresolved_url("question_url", 10, 0)
    # print(data)
    # id = ["2362246"]
    # update_url_resolved(id)
    # print()
    # a = get_png_list()
    # b = load_img_src()
    # c = set(a).difference(set(b))
    # print(c)
    target = ['2b304400-fb23-11e9-847f-55f975649075', 'c5e0ae10-1b08-11ea-a1c6-035417be02d6',
              '34c30fa0-f95a-11e9-bead-fd2cb01958df', 'b51716c0-fb47-11e9-904f-8f35efb1f477']
    print(get_png_list(target))
