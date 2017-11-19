'''
Common variables for the modlinker.
'''
from os import environ
import re

# configuration
MAX_RESULTS = 10
MAX_LENGTH = 9900 # real max is 10000, leave a bit of wiggle room
# TODO: Dynamically get the current alpha number
CURRENT_ALPHA = environ['RIMWORLD_CURRENT_ALPHA'] # default tag for the current alpha

# secrets for reddit
REDDIT = {
    "username": environ['REDDIT_USER'],
    "password": environ['REDDIT_PASSWORD'],
    "client_id": environ['REDDIT_CLIENT_ID'],
    "client_secret": environ['REDDIT_CLIENT_SECRET'],
    "user_agent": 'python:rimworld-modlinker:v1.1 (by /u/FluffierThanThou)',
    "subreddits": environ['REDDIT_LISTEN_TO']
}

# secrets for steam
STEAM = {
    "key": environ['STEAM_KEY']
}

# only used for creating html links
STEAM_WORKSHOP_URL = 'http://steamcommunity.com/workshop/browse/?{params}'
STEAM_WORKSHOP_PARAMS = dict(
    appid=294100,               # RimWorld
    browsesort="textsearch"     # Full text (description) search?
)

# footer text
FOOTER = ( "\n\n*****\n^(I'm a bot | ) [^source](https://github.com/FluffierThanThou/reddit-modlinker)"
           " ^| [^commands](https://github.com/FluffierThanThou/reddit-modlinker/blob/master/bot/COMMANDS.MD#link-to-a-mod-or-scenario-for-a-specific-alpha-of-rimworld)"
           " ^| [^stats](http://modlinker-stats.karel-kroeze.nl/)"
           " ^(| I was made by )[^/u\/FluffierThanThou](/user/FluffierThanThou)" )

# request pattern matches
_regexFlags = re.IGNORECASE + re.MULTILINE # pylint: disable=invalid-name
REGEXES = [
    # pylint: disable=line-too-long
    # link to a single mod, with a single keyword
    # e.g. `linkmod: Colony Manager` does a steam search for "Colony Manager" and shows the top result
    # 1; alpha?, 2; mod|scenario, 3; query
    dict(regex=re.compile(r".*?there's an? ?(?:\[?(?:a|b|alpha |beta )(\d{2})\]?)? (mod|scenario) for that: (.*?)(?:,|;|:|\.|$)", _regexFlags), # https://regexr.com/3gqbv
         description="there's a mod for that"),
    dict(regex=re.compile(r".*?link ?(?:\[?(?:a|b|alpha |beta )(\d{2})\]?)? ?(mod|scenario):? (.*?)(?:,|;|:|\.|$)", _regexFlags), # https://regexr.com/3gqc2
         description="linkmod"),

    # link to a number of mods, for each of a number of keywords
    # e.g. `there's 4 A17 mods for that: manager, tab, fluffy` does a steam search for
    # "manager", "tab" and "fluffy" separately,
    # and shows the top 4 results for each.
    # 1; count?, 2; alpha?, 3; mod|scenario, 4; query
    dict(regex=re.compile(r".*?link\s?(\d*)? ?(?:\[?(?:a|b|alpha |beta )(\d{2})\]?)? ?(mod|scenario)s:? (.*?)(?:;|:|\.|$)", _regexFlags), # https://regex101.com/r/bS5mG3/7
         description="there are mods for that"),
    dict(regex=re.compile(r".*?there(?:'s| are) (\d*)? ?(?:\[?(?:a|b|alpha |beta )(\d{2})\]?)? ?(mod|scenario)s? for that:? (.*?)(?:;|:|\.|$)", _regexFlags), # https://regex101.com/r/bS5mG3/9
         description="linkmods")
    # note that lists are extracted as a block, and further split up in the ModRequest factories.
]
