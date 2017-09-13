# core stuff
import os
import sys
import re
import logging
import urllib2 as http
import urllib
import time
from collections import deque

# reddit api
import praw

# scraping html
from bs4 import BeautifulSoup as bs

# configuration
query_url = 'http://steamcommunity.com/workshop/browse/?{params}'
regexFlags = re.IGNORECASE + re.MULTILINE
MAX_RESULTS = 10
MAX_LENGTH = 9900 # real max is 10000, leave a bit of wiggle room
REDDITS = "RimWorld+TalesFromRimWorld+ShitRimWorldSays+SpaceCannibalism"

# secrets, (mostly) defined in environment
config = {
    "username": os.environ['REDDIT_USER'],
    "password": os.environ['REDDIT_PASSWORD'],
    "client_id": os.environ['REDDIT_CLIENT_ID'],
    "client_secret": os.environ['REDDIT_CLIENT_SECRET'],
    "user_agent": 'python:rimworld-modlinker:v1.0 (by /u/FluffierThanThou)'
}

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

class Mod:
    '''
    A simple Mod class to extract the relevant titles, names and urls from the scraped html <div> tag.
    '''
    title = ""
    url = ""
    authorName = ""
    authorUrl = ""

    def __init__( self, mod ):
        self.title = mod.select( "div.workshopItemTitle" )[0].string.encode( 'utf-8', 'replace' )
        self.url = mod.find( "a" ).get( "href" ).encode( 'utf-8', 'replace' )
        author = mod.select( "div.workshopItemAuthorName a" )[0]
        self.authorName = author.string.encode( 'utf-8', 'replace' )
        self.authorUrl = author.get( "href" ).encode( 'utf-8', 'replace' )

    def __repr__( self ):
        return( ( self.title + " by " + self.authorName ).encode( 'ascii', 'replace' ) )
    
    def __len__( self ):
        return 1

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
            logging.error( "bad request: %", request )
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

def searchWorkshop( request ):
    '''
    Scrape the Steam Workshop page for results, return a list of Mod objects
    '''
    # fetch workshop search results (thankfully this is a simple GET form)
    url = request.getUrl()
    logging.debug("GET %s", url )
    raw = http.urlopen(url).read()
    logging.debug(raw)

    # parse it for mod entries
    mods = [ Mod( mod ) for mod in bs( raw, "html.parser" ).select( "div.workshopItem" ) ]
    logging.info( "Found %i results for %s", len( mods ), request )
    return mods

def getCommentsDone():
    '''
    Get a list of comment id's we've already replied to.
    '''
    if not os.path.isfile("comments.txt"):
        logging.info( "Creating comments.txt" )
        commentsDone = []
    else:
        with open("comments.txt", "r") as f:
            logging.info( "Reading comments.txt" )
            commentsDone = filter( None, f.read().split("\n") )
            logging.info( "We have replied to %i comments so far...", len( commentsDone ) )
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
        logging.warning( "comment.refresh failed" )
        logging.error( str( error ) )
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
    info['countShown'] = min( len( mods ), request.count )

    # chop mods array to requested size
    mods = mods[:request.count]

    # generate result overview
    if len( mods ) > 1:
        result = "Mod | Author \n :-|-: \n"
        for mod in mods:
            result += "[{}]({}) | by [{}]({})\n".format( mod.title, mod.url, mod.authorName, mod.authorUrl )
        result += "\n\n^(Workshop search for) [^(`{request.query}`)]({request_url}) ^(gave {count} results, I'm showing you the top {countShown} results)".format( **info )
    elif mods:
        mod = mods[0]
        result = "[{}]({}) by [{}]({})".format( mod.title, mod.url, mod.authorName, mod.authorUrl )
        result += "\n\n^(Workshop search for) [^(`{request.query}`)]({request_url}) ^(gave {count} results, I'm showing you the top result)".format( **info )
    else:
        result = "^(Workshop search for) [^(`{request.query}`)]({request_url}) ^(gave {count} results)".format( **info )
    logging.debug( result )
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
                logging.warning( "rate limit exceeded. Sleeping for 1 minute." )
                logging.info( error.message )
                time.sleep( 60 )
            else:
                raise

# start the bot
reddit = praw.Reddit( **config )
stream = reddit.subreddit(REDDITS).stream
commentsDone = getCommentsDone();

for comment in stream.comments():
    logging.info( "new comment: %s", comment.id )
    logging.debug( "%s", comment.body.encode( 'ascii', 'replace' ) )

    # skip if already processed
    if comment.id in commentsDone:
        logging.info( "comment.id known, skipping" )
        continue

    # skip if made by me
    if comment.author.name == config['username']:
        logging.info( "comment made by me, skipping" )
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
        logging.info( "no requests, skipping" )
        continue

    # do a final check to see if we haven't already commented to this request
    if hasReplyBy( comment, config['username'] ):
        logging.info( "already replied to comment, skipping" )
        commentDone( comment.id, commentsDone )
        continue

    # get a queue ready for results
    parts = deque()

    # for each search term;
    for request in requests:
        # get a list of results
        mods = searchWorkshop( request )

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
            logging.warning( "comment too long (%d/%d), skipping", len( part ) + len( footer ), MAX_LENGTH )
            logging.debug( part )
            continue

        # else requeue this part, and post a reply
        else:
            parts.appendleft( part )
            logging.info( "replying to %s", comment.id )
            logging.debug( reply )
            handle_ratelimit( comment.reply, reply + footer )

            # reset reply
            reply = ""
    
    # if we exited the last block with a non "" reply, we still have a non-full reply to make
    if reply:
        logging.info( "replying to %s", comment.id )
        logging.debug( reply )
        handle_ratelimit( comment.reply, reply + footer )
                     
    # done!
    commentDone( comment.id, commentsDone )
    logging.info( "Succesfully handled comment %s", comment.id )
