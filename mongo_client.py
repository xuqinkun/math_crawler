from pymongo import MongoClient
from pymongo.errors import *

client = MongoClient('localhost', 27017)
db = client['math_questions']


def insert_one(collection='', doc={}):
    try:
        math_questions = db[collection]  # Get collection math_questions
        math_questions.insert_one(doc)
        return True
    except DuplicateKeyError as e:
        print(e.details)
        return False


def insert_many(collection='', docs=[]):
    try:
        math_questions = db[collection]  # Get collection math_questions
        math_questions.insert_many(docs)
        return True
    except BulkWriteError as e:
        print(e.details)
        return False
