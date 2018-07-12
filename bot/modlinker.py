'''
This is the main modlinker module. It contains the main script loop, and calls
the reddit and workshop modules where needed.
'''
import logging
from collections import deque

from commands import ModRequest
import formatting
import reddit
import workshop
import database
from common import REDDIT

# set up logging
logging.basicConfig(format='%(module)s :: %(levelname)s :: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__) # pylint: disable=invalid-name

# start the bot
# get a comment stream
stream = reddit.getStream(REDDIT['subreddits']) # pylint: disable=invalid-name

# consume new comments for ever and ever
for comment in stream.comments():
    redditor = comment.author.name
    log.info("new comment :: %s", comment.id)
    log.debug("%s", comment.body.encode('ascii', 'replace'))

    # skip if made by me
    if redditor == REDDIT['username']:
        log.info("comment made by me, skipping")
        continue
    
    # get requests for this post
    requests = []
    for request in ModRequest.fromPost(comment.body):
        requests.append(request)

    # skip if there are no requests for this comments
    if not requests:
        log.info("no requests, skipping")
        continue

    # do a final check to see if we haven't already commented to this request
    if reddit.hasReplyBy(comment, REDDIT['username']):
        log.info("already replied to comment, skipping")
        continue

    # get a queue ready for results
    parts = deque()

    # for each search term;
    for request in requests:
        # get a list of results
        log.debug( request )
        mods = workshop.search( request )

        # generate a formatted result table/line, and add it to the queue
        parts.append( formatting.formatResults(request, mods) )

        # add mod to our 'analytics' database
        for mod in mods:
            database.log_mod(redditor, mod)

    # get post(s)
    posts = formatting.createPosts(parts)
    for index, post in enumerate(posts):
        log.debug("reply %s: \n%s", index, post)
        reply = reddit.handle_ratelimit(comment.reply, post)
        try:
            permalink = reply.permalink()
        except TypeError:
            permalink = reply.permalink
        database.log_post(redditor, post, reply.submission.title, permalink)
        log.info("replied to %s (%s/%s): https://www.reddit.com%s",
                 comment.id, index+1, len(posts), permalink)

    # done!
    log.info("Succesfully handled comment %s", comment.id)
