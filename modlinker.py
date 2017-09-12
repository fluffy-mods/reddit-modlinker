# core stuff
import os
import sys
import re
import logging
import urllib2 as http
import time
from collections import deque

# reddit api
import praw

# scraping html
from bs4 import BeautifulSoup as bs

# configuration
query_url = 'http://steamcommunity.com/workshop/browse/?appid=294100&searchtext={}&childpublishedfileid=0&browsesort=textsearch&section=home'
regexFlags = re.IGNORECASE + re.MULTILINE
MAX_RESULTS = 10
MAX_LENGTH = 9900 # real max is 10000, leave a bit of wiggle room

# secrets, (mostly) defined in environment
config = {
    "username": os.environ['REDDIT_USER'],
    "password": os.environ['REDDIT_PASSWORD'],
    "client_id": os.environ['REDDIT_CLIENT_ID'],
    "client_secret": os.environ['REDDIT_CLIENT_SECRET'],
    "user_agent": 'python:rimworld-modlinker:v1.0 (by /u/FluffierThanThou)'
}

# footer text
footer = "\n\n*****\n^(I'm a bot | ) [^(read more about me here)](https://github.com/FluffierThanThou/reddit-modlinker) ^(| I was made by /u/FluffierThanThou)"

# request pattern matches
regexes = [
    # link to a single mod, with a single keyword
    # e.g. `linkmod: Colony Manager` does a steam search for "Colony Manager" and shows the top result
    re.compile(r".*?there's a mod for that: (.*?)(?:,|;|:|\.|$)", regexFlags),
    re.compile(r".*?linkmod:? (.*?)(?:,|;|:|\.|$)", regexFlags),

    # link to a number of mods, for each of a number of keywords
    # e.g. `there's 4 mods for that: manager, tab, fluffy` does a steam search for "manager", "tab" and "fluffy" separately, and 
    # shows the top 4 results for each.
    re.compile(r".*?link\s?(\d*)?\s?mods:? (.*?)(?:;|:|\.|$)", regexFlags), # https://regex101.com/r/bS5mG3/3
    re.compile(r".*?there(?:'s| are) (\d*)? ?mods? for that:? (.*?)(?:;|:|\.|$)", regexFlags) # https://regex101.com/r/bS5mG3/4
]

# set up logging
logging.basicConfig(format='%(asctime)20s :: %(module)s :: %(levelname)s :: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO )

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
    query = ""
    count = ""

    def __init__( self, query, count = 1 ):
        self.query = query
        if isinstance( count, basestring ):
            count = int( count )
        if count > MAX_RESULTS:
            count = MAX_RESULTS
        self.count = count

    @classmethod
    def fromTuple( cls, request ):
        parts = re.split( r',|and', request[1] )
        count = request[0] if request[0] else 1
        return [ cls( part.strip(), count ) for part in parts ]
        
    @classmethod
    def fromString( cls, request ):
        return [ cls( request ) ]
    
    @classmethod
    def fromQuery( cls, request ):
        if isinstance( request, tuple ):
            return cls.fromTuple( request )
        if isinstance( request, basestring ):
            return cls.fromString( request )

    def __repr__( self ):
        return "Request for {} mods matching {}".format( self.count, self.query )

def searchWorkshop( query ):
    '''
    Scrape the Steam Workshop page for results, return a list of Mod objects
    '''
    # fetch workshop search results (thankfully this is a simple GET form)
    logging.debug("GET %s", query_url.format(http.quote(query)))
    raw = http.urlopen( query_url.format( http.quote( query ) ) ).read()
    logging.debug( raw )

    # parse it for mod entries
    mods = [ Mod( mod ) for mod in bs( raw, "html.parser" ).select( "div.workshopItem" ) ]
    logging.info( "Found %i results for %s", len( mods ), query )
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
    info['request_url'] = query_url.format( http.quote( request.query ) )
    info['count'] = len( mods )

    # chop mods array to size
    print request, request.count, dir(request)
    mods = mods[:request.count]

    # generate result overview
    if len( mods ) > 1:
        result = "Mod | Author \n :-|-: \n"
        for mod in mods:
            result += "[{}]({}) | by [{}]({})\n".format( mod.title, mod.url, mod.authorName, mod.authorUrl )
        result += "\n\n^(Workshop search for) [^(`{request.query}`)]({request_url}) ^(gave {count} results, I'm showing you the top {request.count} results)".format( **info )
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

subreddit = reddit.subreddit('bottesting')

commentsDone = getCommentsDone();

for comment in subreddit.stream.comments():
    logging.info( "new comment: %s", comment.id )
    logging.debug( "%s", comment.body.encode( 'ascii', 'replace' ) )

    requests = [ request for regex in regexes for query in regex.findall( comment.body ) for request in ModRequest.fromQuery( query ) ]

    # skip if already processed
    if comment.id in commentsDone:
        logging.info( "comment.id known, skipping" )
        continue

    # skip if made by me
    if comment.author.name == config['username']:
        logging.info( "comment made by me, skipping" )
        continue

    # skip if there are no requests for this comments
    if not requests:
        logging.info( "no requests, skipping" )
        continue

    # do a final check to see if we haven't already commented to this request
    if hasReplyBy( comment, config['username'] ):
        logging.info( "already replied to comment, skipping" )
        commentDone( comment.id, commentsDone )
        continue

    # get reply object ready
    parts = deque()

    # for each search term;
    for request in requests:
        # get a list of results
        mods = searchWorkshop( request.query )

        # generate a formatted result table/line
        parts.append( formatResults( request, mods ) )
    
    # paste parts that fit in one comment together,
    # spread out over multiple comments if need be
    reply = ""
    while parts and len( reply ) + len( footer ) < MAX_LENGTH:
        # get the next part
        part = parts.popleft()

        # attach it if it fits
        if len( part ) + len( reply ) + len( footer ) <= MAX_LENGTH:
            reply += "\n\n" + part

        # remove it if it could never fit
        elif len( part ) + len( footer ) > MAX_LENGTH:
            logging.warning( "comment too long (%d/%d), skipping", len( part ) + len( footer ), MAX_LENGTH )
            logging.debug( part )
            continue

        # else reattach this part, and post a reply
        else:
            parts.appendleft( part )
            logging.info( "replying to %s", comment.id )
            logging.debug( reply )
            # handle_ratelimit( comment.reply, reply + footer )

            # reset reply
            reply = ""
                     
    # done!
    commentDone( comment.id, commentsDone )
    logging.info( "Succesfully handled comment %s", comment.id )
