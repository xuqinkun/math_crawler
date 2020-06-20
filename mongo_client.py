from pymongo import MongoClient
from pymongo.errors import *
import utils
from config import *


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
        print(e.details)
        return False
    except Exception as e:
        print(e)
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
        print(e.details)
        return False
    except Exception as e:
        print(e)
        return False


# Load $num urls from the start item
def load_unresolved_url(num=0, start=0, criteria={}):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COLLECTION_URL]
        criteria[RESOLVED] = False
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
        filter = {PHONE: cookies[PHONE]}
        collection.update(spec=filter, document=cookies, upsert=True)


def load_cookies(phone_number=""):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COOKIE]
        cookies = {}
        for doc in collection.find({ACCOUNT: phone_number}):
            cookies = doc
        return cookies


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
            if key == COLLECTION_IMAGE:
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
        collection = db[COLLECTION_IMAGE]
        docs = collection.find({})
        png_list = []
        for doc in docs:
            png_list.append(doc[UUID])
        return png_list


def get_unresolved_url_count():
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[QUESTION_URL]
        return collection.count({RESOLVED: False})


def get_accounts():
    """
    From mongodb get id and password data
    :return:
    """
    account_list = []
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        collection = client.math_questions.account
        for account in list(collection.find()):
            phone = account['phone']
            pwd = utils.rsa_decrypt(account['password'])
            account_list.append({'phone': phone, 'password': pwd})
    return account_list


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
    target = ['c5e0ae10-1b08-11ea-a1c6-035417be02d6']
    print(get_png_list(target))
