import os
import re

# configuration
MAX_RESULTS = 10
MAX_LENGTH = 9900 # real max is 10000, leave a bit of wiggle room

# secrets for reddit
REDDIT = {
    "username": os.environ['REDDIT_USER'],
    "password": os.environ['REDDIT_PASSWORD'],
    "client_id": os.environ['REDDIT_CLIENT_ID'],
    "client_secret": os.environ['REDDIT_CLIENT_SECRET'],
    "user_agent": 'python:rimworld-modlinker:v1.1 (by /u/FluffierThanThou)',
    "subreddits": os.environ['REDDIT_LISTEN_TO']
}

# secrets for steam
STEAM = {
    "key": os.environ['STEAM_KEY']
}

# only used for creating html links
STEAM_WORKSHOP_URL = 'http://steamcommunity.com/workshop/browse/?{params}'
STEAM_WORKSHOP_PARAMS = dict(
    appid=294100,               # RimWorld
    browsesort="textsearch"     # Full text (description) search?
)

# footer text
FOOTER = "\n\n*****\n^(I'm a bot | ) [^(read more about me here)](https://github.com/FluffierThanThou/reddit-modlinker) ^(| I was made by )[^/u\/FluffierThanThou](/user/FluffierThanThou)"

# request pattern matches
_regexFlags = re.IGNORECASE + re.MULTILINE # pylint: disable=invalid-name
REGEXES = [
    # link to a single mod, with a single keyword
    # e.g. `linkmod: Colony Manager` does a steam search for "Colony Manager" and shows the top result
    re.compile(r".*?there's a (mod|scenario) for that: (.*?)(?:,|;|:|\.|$)", _regexFlags),
    re.compile(r".*?link(mod|scenario):? (.*?)(?:,|;|:|\.|$)", _regexFlags),

    # link to a number of mods, for each of a number of keywords
    # e.g. `there's 4 mods for that: manager, tab, fluffy` does a steam search for "manager", "tab" and "fluffy" separately, and
    # shows the top 4 results for each.
    re.compile(r".*?link\s?(\d*)?\s?(mod|scenario)s:? (.*?)(?:;|:|\.|$)", _regexFlags), # https://regex101.com/r/bS5mG3/3
    re.compile(r".*?there(?:'s| are) (\d*)? ?(mod|scenario)s for that:? (.*?)(?:;|:|\.|$)", _regexFlags) # https://regex101.com/r/bS5mG3/4
    # note that lists are extracted as a block, and further split up in the ModRequest factories.
]
