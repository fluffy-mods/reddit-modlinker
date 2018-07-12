'''
recognize modlinker commands in strings, and generate requests
'''
import logging
import re
import urllib

from common import CURRENT_VERSION, MAX_RESULTS, STEAM_WORKSHOP_PARAMS, STEAM_WORKSHOP_URL

log = logging.getLogger(__name__)

# request pattern matches
_regexFlags = re.IGNORECASE + re.MULTILINE # pylint: disable=invalid-name
REGEXES_SINGLE = [
    # pylint: disable=line-too-long
    # link to a single mod, with a single keyword
    # e.g. `linkmod: Colony Manager` does a steam search for "Colony Manager" and shows the top result
    # returns query, type, alpha?, version?
    re.compile(r".*?there's an? (?:(?:\[?(?:a|b|alpha|beta) ?(?P<alpha>\d{2})\]?)|(?:(?:version|v)? ?(?P<version>\d\.\d)))? ?(?P<type>mod|scenario) for that: (?P<query>.*?)(?:,|;|:|\.|\)|$)", _regexFlags), # https://regex101.com/r/SzY4cq/2
    re.compile(r".*?link ?(?:(?:\[?(?:a|b|alpha|beta) ?(?P<alpha>\d{2})\]?)|(?:\[?(?:v|version)? ?(?P<version>\d\.\d)\]?))? ?(?P<type>mod|scenario):? (?P<query>.*?)(?:,|;|:|\.|\)|$)", _regexFlags), # https://regex101.com/r/nzl7di/2
]

REGEXES_MULTIPLE = [
    # link to a number of mods, for each of a number of keywords
    # e.g. `there's 4 A17 mods for that: manager, tab, fluffy` does a steam search for
    # "manager", "tab" and "fluffy" separately,
    # and shows the top 4 results for each.
    # query, type, count?, alpha?, version?
    re.compile(r".*?link\s?(?P<count>\d+)?\s?(?:(?:\[?(?:a|b|alpha|beta)\s?(?P<alpha>\d{2})\]?)|(?:\[?(?:v|version)?\s?(?P<version>\d\.\d)\]?))?\s?(?P<type>mod|scenario)s:?\s?(?P<query>.*?)(?:;|:|\.|$)", _regexFlags), # https://regex101.com/r/bS5mG3/12
    re.compile(r".*?there(?:'s| are) (?P<count>\d+)? ?(?:(?:\[?(?:a|b|alpha|beta)\s?(?P<alpha>\d{2})\]?)|(?:\[?(?:v|version)?\s?(?P<version>\d\.\d)\]?))?\s?(?P<type>mod|scenario)s? for that:? (?P<query>.*?)(?:;|:|\.|$)", _regexFlags), # https://regex101.com/r/xerzQX/2
    # note that lists are extracted as a block, and further split up in the ModRequest factories.
]

def getTag(alpha = None, version = None):
    if version:
        return version
    if alpha:
        if isinstance(alpha, str):
            alpha = float(alpha)
        return alpha/100
    return CURRENT_VERSION

class ModRequest:
    '''
    Simple wrapper for search term + count
    '''
    def __init__(self, mod, query, version, count = 1):
        if isinstance(count, str):
            count = int(count)
        if count > MAX_RESULTS:
            count = MAX_RESULTS
        self.mod = mod
        self.query = query
        self.count = count
        self.tags = []
        if version:
            self.tags.append(str(version))
        else:
            self.tags.append(str(CURRENT_VERSION))

        if self.mod:
            self.tags.append("Mod")
        else:
            self.tags.append("Scenario")

    def getUrl(self):
        params = dict(STEAM_WORKSHOP_PARAMS)
        params['requiredtags[]'] = self.tags
        params['searchtext'] = self.query
        return STEAM_WORKSHOP_URL.format(params = urllib.parse.urlencode(params, True))

    @classmethod
    def fromPost(cls, post):
        requests = []

        for regex in REGEXES_SINGLE:
            for match in regex.finditer(post):
                data = match.groupdict()
                requests.append(ModRequest(data['type'] == "mod", data['query'], getTag(data['alpha'], data['version']), 1))

        for regex in REGEXES_MULTIPLE:
            for match in regex.finditer( post ):
                data = match.groupdict()
                queries = re.split(r',', data['query'])
                count = 1
                if (data['count']):
                    count = data['count']
                for query in queries:
                    requests.append(ModRequest(data['type'] == "mod", query.strip(), getTag(data['alpha'], data['version']), count))
        
        return requests

    def __repr__(self):
        print(vars(self))

    def __str__(self):
        return "Request for {!s} [{!s}] matching {!s}".format(self.count, ", ".join(self.tags), self.query)
