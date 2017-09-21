# core stuff
import os
import sys
import re
import logging
import time
import urllib
from collections import deque

# reddit api
import praw

# our simple steam workshop wrapper
import workshop

# configuration
query_url = 'http://steamcommunity.com/workshop/browse/?{params}'
regexFlags = re.IGNORECASE + re.MULTILINE
MAX_RESULTS = 10
MAX_LENGTH = 9900 # real max is 10000, leave a bit of wiggle room
REDDITS = "bottesting"

# secrets, (mostly) defined in environment
config = {
    "username": os.environ['REDDIT_USER'],
    "password": os.environ['REDDIT_PASSWORD'],
    "client_id": os.environ['REDDIT_CLIENT_ID'],
    "client_secret": os.environ['REDDIT_CLIENT_SECRET'],
    "user_agent": 'python:rimworld-modlinker:v1.0 (by /u/FluffierThanThou)'
}

# only used for creating html links
steam_request_params = dict(
    appid=294100,               # RimWorld
    browsesort="textsearch"     # Full text (description) search?
)

# footer text
footer = "\n\n*****\n^(I'm a bot | ) [^(read more about me here)](https://github.com/FluffierThanThou/reddit-modlinker) ^(| I was made by )[^/u\/FluffierThanThou](/user/FluffierThanThou)"

# request pattern matches
regexes = [
    # link to a single mod, with a single keyword
    # e.g. `linkmod: Colony Manager` does a steam search for "Colony Manager" and shows the top result
    re.compile(r".*?there's a (mod|scenario) for that: (.*?)(?:,|;|:|\.|$)", regexFlags),
    re.compile(r".*?link(mod|scenario):? (.*?)(?:,|;|:|\.|$)", regexFlags),

    # link to a number of mods, for each of a number of keywords
    # e.g. `there's 4 mods for that: manager, tab, fluffy` does a steam search for "manager", "tab" and "fluffy" separately, and 
    # shows the top 4 results for each.
    re.compile(r".*?link\s?(\d*)?\s?(mod|scenario)s:? (.*?)(?:;|:|\.|$)", regexFlags), # https://regex101.com/r/bS5mG3/3
    re.compile(r".*?there(?:'s| are) (\d*)? ?(mod|scenario)s for that:? (.*?)(?:;|:|\.|$)", regexFlags) # https://regex101.com/r/bS5mG3/4
    # note that lists are extracted as a block, and further split up in the ModRequest factories.
]

# set up logging
logging.basicConfig( format='%(module)s :: %(levelname)s :: %(message)s', level=logging.INFO )
log = logging.getLogger(__name__)

class ModRequest:
    '''
    Simple wrapper for search term + count
    '''
    def __init__( self, mod, query, count = 1, tags = [] ):
        if isinstance( count, basestring ):
            count = int( count )
        if count > MAX_RESULTS:
            count = MAX_RESULTS
        self.mod = mod
        self.query = query
        self.count = count
        self.tags = list( tags )
        if self.mod:
            self.tags.append( "Mod" )
        else: 
            self.tags.append( "Scenario" )

    def getUrl( self ):
        params = dict( steam_request_params )
        params['requiredtags[]'] = self.tags
        params['searchtext'] = self.query
        return query_url.format( params = urllib.urlencode( params, True ) )

    @classmethod
    def fromQuery( cls, request ):
        mod = True
        query = ""
        count = 1

        if isinstance( request, basestring ):
            return [ cls( True, request ) ]

        if not isinstance( request, tuple ):
            log.error( "bad request: %s", request )
            return []

        # e.g. link{0: mod|scenario}: {2: query string}
        if len(request) == 2:
            mod = request[0] == "mod"
            return [ cls( mod, request[1] ) ]

        # e.g. link{0: count}{1: mod|scenario}s: {2: query string}
        if len(request) == 3:
            count = request[0] if request[0] else 1
            mod = request[1] == "mod"
            parts = re.split( r',', request[2] )
            return [ cls( mod, part.strip(), count ) for part in parts ]

    def __repr__( self ):
        return "Request for {} {}s matching {}".format( self.count, "mod" if self.mod else "scenario", self.query )

def getCommentsDone():
    '''
    Get a list of comment id's we've already replied to.
    '''
    if not os.path.isfile("comments.txt"):
        log.info( "Creating comments.txt" )
        commentsDone = []
    else:
        with open("comments.txt", "r") as f:
            log.info( "Reading comments.txt" )
            commentsDone = filter( None, f.read().split("\n") )
            log.info( "We have replied to %i comments so far...", len( commentsDone ) )
    return commentsDone


def commentDone( comment_id, commentsDone ):
    '''
    Add a comment id to the list of comments replied to.
    '''
    commentsDone.append( comment_id )
    with open("comments.txt", "a") as f:
        f.write(comment_id + "\n")

def hasReplyBy( comment, username ):
    # refresh has a nasty tendency to fail on fresh posts.
    # since this is really only meant to avoid duplication on a restart of the script, 
    # and fresh posts are unlikely to have replies, just assume we haven't replied yet.
    # TODO: Selectively catch, raise other errors.
    try:
        comment.refresh()
    except Exception( error ):
        log.warning( "comment.refresh failed" )
        log.error( str( error ) )
        return False

    for reply in comment.replies:
        if reply.author.name == username:
            return True
    return False

def formatResults( request, mods ):
    '''
    Create a nice reddit layout table for our response.
    '''
    # prepare info dict
    info = {}
    info['request'] = request
    info['request_url'] = request.getUrl()
    info['count'] = len( mods )

    # generate result overview
    if len( mods ) > 1:
        result = "Mod | Author \n :-|-: \n"
        for mod in mods:
            result += "[{}] [{}]({}) | by [{}]({})\n".format( mod.alpha, mod.title, mod.url, mod.authorName, mod.authorUrl )
        result += "\n\n^(Results for ) [^(`{request.query}`)]({request_url})^(. I'm showing you the top {count} results, there may be more.)".format( **info )
    elif mods:
        mod = mods[0]
        result = "[{}] [{}]({}) by [{}]({})".format( mod.alpha, mod.title, mod.url, mod.authorName, mod.authorUrl )
        result += "\n\n^(Results for) [^(`{request.query}`)]({request_url})^(. I'm showing you the top result, there may be more.)".format( **info )
    else:
        result = "Sorry, but a search for [`{request.query}`]({request_url}) gave no results.".format( **info )
    log.debug( result )
    return result

def handle_ratelimit(func, *args, **kwargs):
    '''
    If we encounter a rate limit exception, sleep for a while and then try again.
    https://gist.github.com/bboe/1860715
    '''
    while True:
        try:
            func(*args, **kwargs)
            break
        except praw.exceptions.APIException as error:
            if error.error_type == "RATELIMIT":
                log.warning( "rate limit exceeded. Sleeping for 1 minute." )
                log.info( error.message )
                time.sleep( 60 )
            else:
                raise

# start the bot
reddit = praw.Reddit( **config )
stream = reddit.subreddit( REDDITS ).stream
commentsDone = getCommentsDone();

for comment in stream.comments():
    log.info( "new comment: %s", comment.id )
    log.debug( "%s", comment.body.encode( 'ascii', 'replace' ) )

    # skip if already processed
    if comment.id in commentsDone:
        log.info( "comment.id known, skipping" )
        continue

    # skip if made by me
    if comment.author.name == config['username']:
        log.info( "comment made by me, skipping" )
        continue

    # for all regexes, get all results, and for all results, get all mod requests.
    requests = [ request for regex in regexes for query in regex.findall( comment.body ) for request in ModRequest.fromQuery( query ) ]
    
    # queries = [ query for regex in regexes for query in regex.findall( comment.body ) ]
    # for query in queries:
    #     print query
    #     for request in ModRequest.fromQuery( query ):
    #         print "\t", request
    #         print "\t", request.getUrl()

    # skip if there are no requests for this comments
    if not requests:
        log.info( "no requests, skipping" )
        continue

    # do a final check to see if we haven't already commented to this request
    if hasReplyBy( comment, config['username'] ):
        log.info( "already replied to comment, skipping" )
        commentDone( comment.id, commentsDone )
        continue

    # get a queue ready for results
    parts = deque()

    # for each search term;
    for request in requests:
        # get a list of results
        mods = workshop.search( request )

        # generate a formatted result table/line, and add it to the queue
        parts.append( formatResults( request, mods ) )
    
    # paste parts that fit in one comment together,
    # spread out over multiple comments if need be
    reply = ""
    while parts and len( reply ) + len( footer ) < MAX_LENGTH:
        # get the next part
        part = parts.popleft()

        # add it to the reply if it fits
        if len( part ) + len( reply ) + len( footer ) <= MAX_LENGTH:
            reply += "\n\n" + part

        # remove it if it could never fit (shouldn't really be possible, unless MAX_REPLIES is raised to 30 and we get some very long mod/author names)
        elif len( part ) + len( footer ) > MAX_LENGTH:
            log.warning( "comment too long (%d/%d), skipping", len( part ) + len( footer ), MAX_LENGTH )
            log.debug( part )
            continue

        # else requeue this part, and post a reply
        else:
            parts.appendleft( part )
            log.info( "replying to %s", comment.id )
            log.debug( reply )
            handle_ratelimit( comment.reply, reply + footer )

            # reset reply
            reply = ""
    
    # if we exited the last block with a non "" reply, we still have a non-full reply to make
    if reply:
        log.info( "replying to %s", comment.id )
        log.debug( reply )
        handle_ratelimit( comment.reply, reply + footer )
                     
    # done!
    commentDone( comment.id, commentsDone )
    log.info( "Succesfully handled comment %s", comment.id )
