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

def update_img_info(img_text_list={}):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COLLECTION_IMAGE]
        count = 0
        for uuid, text in img_text_list.items():
            print(uuid,text)
            if text != "":
                collection.update_one(filter={UUID: uuid}, update={"$set": {RESOLVED: True, PLAIN_TEXT: text}})
                count = count + 1
        print("%d images text updated "% count)
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
        png_dict = {}
        for doc in docs:
            if doc[RESOLVED] == False:
                png_dict[doc[UUID]] = doc["src"]
        return png_dict


def get_unresolved_url_count(criteria):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[QUESTION_URL]
        criteria[RESOLVED] = False
        return collection.count(criteria)


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


def get_img_of_options():
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
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


def get_img_of_title():
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
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


def remove_img(uuid_list):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[DB]
        collection = db[COLLECTION_IMAGE]
        ret = collection.delete_many({UUID: {"$in": uuid_list}})
        print(ret.deleted_count)


if __name__ == '__main__':
    img_list1 = get_img_of_title()
    img_list2 = get_img_of_options()