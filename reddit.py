import logging
import time

import praw

from common import REDDIT

log = logging.getLogger(__name__) # pylint: disable=invalid-name

def hasReplyBy( comment, username ):
    """
    Returns true if `comment` has a first-level reply made by `username`.
        :param comment: reddit.Comment
        :param username: string username
    """
    # refresh has a nasty tendency to fail on fresh posts.
    # since this is really only meant to avoid duplication on a restart of the script,
    # and fresh posts are unlikely to have replies, just assume we haven't replied yet.
    # TODO: Selectively catch, raise other errors.
    try:
        comment.refresh()
    except Exception as error:
        log.warning( "comment.refresh failed" )
        log.error( str( error ) )
        return False

    for reply in comment.replies:
        if reply.author.name == username:
            return True
    return False

def handle_ratelimit(func, *args, **kwargs):
    '''
    If we encounter a rate limit exception, sleep for a while and then try again.
    https://gist.github.com/bboe/1860715
    '''
    while True:
        try:
            return func(*args, **kwargs)
        except praw.exceptions.APIException as error:
            if error.error_type == "RATELIMIT":
                log.warning( "rate limit exceeded. Sleeping for 1 minute." )
                log.info( error.message )
                time.sleep( 60 )
            else:
                raise

def getStream( reddits ):
    return praw.Reddit( **REDDIT ).subreddit( reddits ).stream

if __name__ == '__main__':
    print REDDIT
    for comment in getStream( REDDIT['subreddits'] ).comments():
        print (comment.body + " by " + comment.author.name).encode("ascii", "replace")