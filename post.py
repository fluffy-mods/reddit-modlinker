import logging
from common import MAX_LENGTH, FOOTER

log = logging.getLogger(__name__)

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

def createPosts( parts ):
    """
    paste parts that fit in one comment together,
    spread out over multiple comments if need be
        :param parts: list of search response strings, see `formatResults`
    """
    posts = []
    reply = ""
    while parts and len( reply ) + len( FOOTER ) < MAX_LENGTH:
        # get the next part
        part = parts.popleft()

        # add it to the reply if it fits
        if len( part ) + len( reply ) + len( FOOTER ) <= MAX_LENGTH:
            reply += "\n\n" + part

        # remove it if it could never fit (shouldn't really be possible, unless MAX_REPLIES is raised to 30 and we get some very long mod/author names)
        elif len( part ) + len( FOOTER ) > MAX_LENGTH:
            log.warning( "comment too long (%d/%d), skipping", len( part ) + len( FOOTER ), MAX_LENGTH )
            log.debug( part )
            continue

        # else requeue this part, and post a reply
        else:
            parts.appendleft( part )
            posts.append( reply + FOOTER )

            # reset reply
            reply = ""

    # if we exited the last block with a non "" reply, we still have a non-full reply to make
    if reply:
        posts.append( reply + FOOTER )

    return posts
