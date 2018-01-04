'''
Service module to handle database logging.
'''
import logging
import os
import datetime
from pymongo import MongoClient

LOG = logging.getLogger(__name__)
CLIENT = MongoClient(os.environ['MONGO_URI'].strip("\""))
DB = CLIENT.teddy

# TODO: rename collections to be more sensible.
# NOTE: that also applies to the node stats frontend!
REQUESTS = DB.requests_collection
PATTERNS = DB.patterns
POSTS = DB.posts

def log_mod(redditor, mod):
    '''
    Log a request for a single mod to the database.
    '''
    record = {
        "requestingRedditor": redditor,
        "mod": mod.toObject()
    }
    log(record, REQUESTS)

def log_pattern(redditor, pattern):
    '''
    Log a pattern use to the database.
    '''
    record = {
        "requestingRedditor": redditor,
        "pattern": pattern
    }
    log(record, PATTERNS)

def log_post(redditor, post, submission, permalink):
    '''
    Log a post we made to the database.
    '''
    record = {
        "requestingRedditor": redditor,
        "post": post,
        "submission": submission,
        "permalink": permalink
    }
    log(record, POSTS)

def log(record, collection):
    '''
    Basic log function, called by all the other loggers.
    @param record: an object to be logged
    @param collection: a pymongo collection object
    '''
    record['timestamp'] = str(datetime.datetime.now())
    try:
        collection.insert_one(record)
    except Exception as err: # pylint: disable=W0703
        LOG.error("%s in %s: .\n%s", type(err), collection, err)

if __name__ == '__main__':
    print(REQUESTS.count(), "requests logged")
    print(PATTERNS.count(), "patterns logged")
    print(POSTS.count(), "posts logged")
