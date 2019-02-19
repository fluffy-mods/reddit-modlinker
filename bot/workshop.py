import logging
import os
import re
import sys

from steam import WebAPI
from common import EPSILON, STEAM, STEAM_WORKSHOP_URL, STEAM_WORKSHOP_PARAMS
from commands import ModRequest

log = logging.getLogger(__name__)

_api = WebAPI(key=STEAM['key'])
_mod_url = "https://steamcommunity.com/sharedfiles/filedetails/?id={}"

_params = {
    # the parts that we're interested in
    "search_text": "", # required
    "requiredtags": [], # required
    "numperpage": 1, # optional

    # static 'settings'
    "query_type": 3, # required, this corresponds to the 'relevance' search mode.
    "return_tags": True, # required, we want to get tags back so we can show the Alpha number.
    "appid": STEAM_WORKSHOP_PARAMS['appid'], # required
    "creator_appid": STEAM_WORKSHOP_PARAMS['appid'], # required
    "match_all_tags": True, # optional
    "cache_max_age_seconds": 0, # optional

    # stuff we don't use, but the API requires
    "cursor": "*",
    "return_details": True,
    "strip_description_bbcode": True,
    "page": 0, # required
    "child_publishedfileid": "", # required
    "days": False, # required
    "excludedtags": False, # required
    "filetype": "0", # required
    "ids_only": False, # required
    "include_recent_votes_only": False, # required
    "omitted_flags": "", # required
    "required_flags": "", # required
    "required_kv_tags": "{}", # required
    "return_children": False, # required
    "return_for_sale_data": False, # required
    "return_kv_tags": False, # required
    "return_metadata": True, # optional
    "return_playtime_stats": False, # required
    "return_previews": False, # required
    "return_short_description": False, # required
    "return_vote_data": False, # required
    "totalonly": False, # required
}

def tagsToAlpha(tags):
    # we get Mod/Scenario, and a version tag. 
    # Just loop over tags and return the first one that doesn't raise a ValueError...
    for tag in tags:
        try:
            tag = float(tag['tag'])
            if tag >= 1 - EPSILON:
                return str(tag)
            if tag >= 0.18 - EPSILON:
                return 'B{:.0f}'.format(tag*100)
            return 'A{:.0f}'.format(tag*100)
        except ValueError:
            continue

def _findAuthor(mod, authors):
    for author in authors:
        if author['steamid'] == mod['creator']:
            return author 
    log.error("no author found for mod %s", mod['title'].encode("ascii", "replace"))

def search(query, count = 1, tags = [], query_type = 3):
    # allow calling with a ModRequest, as well as directly
    try:
        _params['search_text'] = query.query
        _params['numperpage'] = query.count
        _params['requiredtags'] = query.tags
    except AttributeError:
        _params['search_text'] = query
        _params['numperpage'] = count
        _params['requiredtags'] = tags
        query = ModRequest(True, query, "1.0", count)
    _params['query_type'] = query_type;    
    
    # raw response
    log.info("search for %s files matching '%s' with tags [%s] and query_type '%s'", _params['numperpage'], _params['search_text'], ", ".join(_params['requiredtags']), _params['query_type'])
    log.info(query.getUrl())
    raw_mods = _api.IPublishedFileService.QueryFiles(**_params)

    # get list of mods
    try:
        mods = raw_mods['response']['publishedfiledetails']
        log.info("found %s results for %s files matching '%s' with tags [%s]", len(mods), _params['numperpage'], _params['search_text'], ", ".join(_params['requiredtags']))
    except:
        log.info("found NO RESULTS for %s files matching '%s' with tags [%s]", _params['numperpage'], _params['search_text'], ", ".join(_params['requiredtags']))      
        return []
    
    # get list of authors
    authorIds = ",".join([ mod['creator'] for mod in mods ])
    raw_authors = _api.ISteamUser.GetPlayerSummaries(steamids = authorIds)
    authors = raw_authors['response']['players']

    # generate a list of Mod objects
    return [ Mod(mod, _findAuthor(mod, authors)) for mod in mods ]

class Mod:
    VERSION_REGEX = re.compile(r"\[?([ab]?\d{2}|v?1\.\d)\]?", re.IGNORECASE) # https://regex101.com/r/ICiCxq/2

    def __init__(self, mod, author):
        self.title = mod['title']
        self.url = _mod_url.format(mod['publishedfileid'])
        self.authorName = author['personaname']
        self.authorUrl = author['profileurl'] + "myworkshopfiles/?appid=" + str(STEAM_WORKSHOP_PARAMS['appid'])
        self.alpha = tagsToAlpha(mod['tags'])
                
    def __repr__(self):
        return "[{}] {} by {} ({}, {})".format(self.alpha, self.title, self.authorName, self.url, self.authorUrl) 
    
    def __len__(self):
        return 1 

    # note that this regex is hardcoded for 1.x versions, as I don't want to make it too confused to a mod giving itself an x.x version.
    def nameIncludesVersion(self):
        match = Mod.VERSION_REGEX.search(self.title)
        if match:
            return True
        return False

    def toObject(self):
        return {
            "title": self.title,
            "url": self.url,
            "author": self.authorName,
            "authorUrl": self.authorUrl
        }

if __name__ == '__main__':
    logging.basicConfig(format='%(module)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    if len(sys.argv) > 1:
        print("looking for: " + sys.argv[1])
        for qt in range(0, 10):
            for result in search(sys.argv[1], 5, ["Mod", "1.0"], qt):
                print("\t\t\t", result)
    else:
        print("testing steam API")
        for mod in search("Pawns are Capable!", 10):
            print("\t" + str(mod))

        # print("testing query recognition")
        # for query in [
        #     'linkmod: ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ, unicode exists.',
        #     "linkB18mod: Better",
        #     "link [B18] mod: Expanded",
        #     "linkA18mod: Extended",
        #     "link beta 18 mod: I'm running out of test query ideas",
        #     "Link Mod: High Caliber",
        #     "there's an alpha 11 mod for that: blurb",
        #     "there's mods for that: josephine, peter, jasper",
        #     "there's 4 mods for that: josephine, peter, jasper",
        #     "there are 20 mods for that: josephine, peter, jasper",
        #     "there are mods for that: josephine, peter, jasper",
        #     "there are mods for that. Other text.",
        #     "You know, there are mods for that: Timmy",
        #     "there's A15 mods for that: josephine, peter, jasper",
        #     "there's 4 A17 mods for that: josephine, peter, jasper",
        #     "there are 20 [A14] mods for that: josephine, peter, jasper",
        #     "there are alpha 12 mods for that: josephine, peter, jasper",
        #     "there are Alpha 14 mods for that. Other text.",
        #     "You know, there are [Alpha 15] mods for that: Timmy",
        #     "link4mods: josephine, peter, jasper",
        #     "linkmods: josephine, peter, jasper",
        #     "link 4 mods: josephine, peter, jasper",
        #     "link mods: josephine, peter, jasper",
        #     "link4[A15]mods: josephine, peter, jasper.",
        #     "link 4 A15 mods josephine, peters, jasper",
        #     "linkmod: timmy!",
        #     "linkA14mod: ancient mods are the best",
        #     "linkscenario: scenarios are for the brave", 
        #     "there's a mod for that: timmy!",
        #     "there's an A16 mod for that: timmy!",
        #     "there's a scenario for that: boris?",
        #     "linkmod : Expanded Prosthetics",
        #     "linkmod :",
        #     "linkmod: Expanded Prosthetics",
        #     "linkmod:",
        #     "linkmod:Expanded Prosthetics",
        #     "linkmod :Expanded Prosthetics",
        #     "linkmod:Expanded Prosthetics",
        #     "linkmod:",
        #     "there are 10 v1.0 mods for that: some text.",
        #     "there are 1.0 mods for that: some more text.",
        #     "there are version 2.0 scenarios for that: probably not",
        #     "link 1.0 mod: awesome sauce!",
        #     "link v2.2 mod: totes!",
        #     "there's a 1.0 mod for that: Peter",
        #     "there's a v1.0 mod for that: Bossman.",
        #     "there's a version 1.0 mod for that: Peter",
        #     "some text (oh by the way, there's a mod for that: Stuff) some more text",
        #     "link 4 v1.0 mods: peter",
        #     "link 1.0 mods: tommy!",
        #     "linkB18mods: tommy!",
        #     "link12B18mods: tommies",
        #     "there are multiple requests in this post. link20mods: fluffierthanthou. link20v1.0mods: mod"
        # ]:
        #     print("\t" + query)
        #     for request in ModRequest.fromPost( query ):
        #         print('\t\t{!s}'.format( request ))
        #         for result in search(request):
        #             print("\t\t\t", result)
        #     # input("Press Enter to continue...")
    print("bye!")