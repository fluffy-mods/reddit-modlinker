import logging
import os
import re
import urllib

from steam import WebAPI

from common import CURRENT_ALPHA, MAX_RESULTS, REGEXES, STEAM, STEAM_WORKSHOP_URL, STEAM_WORKSHOP_PARAMS

log = logging.getLogger(__name__)

_api = WebAPI( key = STEAM['key'] )
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
    "cache_max_age_seconds": 120, # optional

    # stuff we don't use, but the API requires
    "page": 1, # required
    "child_publishedfileid": "", # required
    "days": 7, # required
    "excludedtags": "", # required
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

_tag_regex = re.compile( r"\d\.(\d{2})" )
def _tagsToAlpha( tags ):
    for tag in tags:
        match = _tag_regex.match( tag['tag'] )
        log.debug( "tag regex: %s, %s", tag['tag'], match )
        if match:
            version = int(match.group(1))
            if version >= 18:
                return "B" + str(version)
            else:
                return "A" + str(version)

_alpha_regex = re.compile( r"\b(?:A|B|Alpha|Beta ?)?(\d{2})\b" )
def alphaToTag( alphastring ):
    match = _alpha_regex.search( str( alphastring ) )
    log.debug( "alpha regex: %s, %s", str( alphastring ), match )
    if match:
        return "0." + match.group(1)

def _findAuthor( mod, authors):
    for author in authors:
        if author['steamid'] == mod['creator']:
            return author 
    log.error( "no author found for mod %s", mod['title'].encode("ascii", "replace"))

def search( query, count = 1, tags = [] ):
    # allow calling with a ModRequest, as well as directly
    try:
        _params['search_text'] = query.query
        _params['numperpage'] = query.count
        _params['requiredtags'] = query.tags
    except AttributeError:
        _params['search_text'] = query
        _params['numperpage'] = count
        _params['requiredtags'] = tags

    # raw response
    log.debug( "search for %s files matching '%s' with tags [%s]", _params['search_text'], _params['numperpage'], ", ".join(_params['requiredtags']))
    raw_mods = _api.IPublishedFileService.QueryFiles( **_params )

    # get list of mods
    try:
        mods = raw_mods['response']['publishedfiledetails']
        log.info( "found %s results for %s files matching '%s' with tags [%s]", len(mods), _params['numperpage'], _params['search_text'], ", ".join(_params['requiredtags']))
    except:
        log.info( "found NO RESULTS for %s files matching '%s' with tags [%s]", _params['numperpage'], _params['search_text'], ", ".join(_params['requiredtags']))      
        return []
    
    # get list of authors
    authorIds = ",".join([ mod['creator'] for mod in mods ])
    raw_authors = _api.ISteamUser.GetPlayerSummaries( steamids = authorIds )
    authors = raw_authors['response']['players']

    # generate a list of Mod objects
    return [ Mod( mod, _findAuthor( mod, authors ) ) for mod in mods ]

class Mod:
    def __init__( self, mod, author ):
        self.title = mod['title']
        self.url = _mod_url.format( mod['publishedfileid'] )
        self.authorName = author['personaname']
        self.authorUrl = author['profileurl'] + "myworkshopfiles/?appid=" + str( STEAM_WORKSHOP_PARAMS['appid'] )
        self.alpha = _tagsToAlpha( mod['tags'] )
                
    def __repr__( self ):
        return "[{}] {} by {} ({}, {})".format( self.alpha, self.title, self.authorName, self.url, self.authorUrl ) 
    
    def __len__( self ):
        return 1

    def nameIncludesAlpha( self ):
        match = _alpha_regex.search( self.title )
        if match:
            return True
        return False

    def toObject( self ):
        return {
            "title": self.title,
            "url": self.url,
            "author": self.authorName,
            "authorUrl": self.authorUrl
        }

class ModRequest:
    '''
    Simple wrapper for search term + count
    '''
    def __init__( self, mod, query, alpha, count = 1 ):
        if isinstance( count, str ):
            count = int( count )
        if count > MAX_RESULTS:
            count = MAX_RESULTS
        self.mod = mod
        self.query = query
        self.count = count
        self.tags = []
        if alpha:
            alpha_tag = alphaToTag( alpha )
            if alpha_tag:
                self.tags.append( alpha_tag )
            else:
                log.error( "Failed to get alpha tag from string: %s", alpha )
        else: 
            self.tags.append( CURRENT_ALPHA )

        if self.mod:
            self.tags.append( "Mod" )
        else: 
            self.tags.append( "Scenario" )

    def getUrl( self ):
        params = dict( STEAM_WORKSHOP_PARAMS )
        params['requiredtags[]'] = self.tags
        params['searchtext'] = self.query
        return STEAM_WORKSHOP_URL.format( params = urllib.parse.urlencode( params, True ) )

    @classmethod
    def fromQuery( cls, request ):
        mod = True
        count = 1

        if isinstance( request, str ):
            return [ cls( True, request ) ]

        if not isinstance( request, tuple ) or len(request) == 2:
            log.error( "bad request: %s", request )
            return []

        # e.g. link{0: A17}{1: mod|scenario}: {2: query string}
        if len(request) == 3:
            if not request[2]:
                log.warning( "empty query" )
                return []
            mod = request[1].lower() == "mod"
            return [ cls( mod, request[2], request[0] ) ]

        # e.g. link{0: count}{1: A17}{2: mod|scenario}s: {2: query string}
        if len(request) == 4:
            count = request[0] if request[0] else 1
            mod = request[2].lower() == "mod"
            parts = re.split( r',', request[3] )
            return [ cls( mod, part.strip(), request[1], count ) for part in parts if part.strip() ]
        
        log.error( "bad request: %s", request )
        return []

    def __repr__( self ):
        try:
            return "Request for {} [{}] matching {}".format( self.count, ", ".join( self.tags), self.query )
        except:
            print(vars(self))

if __name__ == '__main__':
    logging.basicConfig( format='%(module)s :: %(levelname)s :: %(message)s', level=logging.INFO )
    print("testing steam API")
    for mod in search( "FluffierThanThou", 10 ):
        print("\t", mod)

    print("testing query recognition")
    for query in [
        'linkmod: ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ, unicode exists.',
        "linkB18mod: Better",
        "link [B18] mod: Expanded",
        "linkA18mod: Extended",
        "link beta 18 mod: I'm running out of test query ideas",
        "Link Mod: High Caliber",
        "there's an alpha 11 mod for that: blurb",
        "there's mods for that: josephine, peter, jasper",
        "there's 4 mods for that: josephine, peter, jasper",
        "there are 20 mods for that: josephine, peter, jasper",
        "there are mods for that: josephine, peter, jasper",
        "there are mods for that. Other text.",
        "You know, there are mods for that: Timmy",
        "there's A15 mods for that: josephine, peter, jasper",
        "there's 4 A17 mods for that: josephine, peter, jasper",
        "there are 20 [A14] mods for that: josephine, peter, jasper",
        "there are alpha 12 mods for that: josephine, peter, jasper",
        "there are Alpha 14 mods for that. Other text.",
        "You know, there are [Alpha 15] mods for that: Timmy",
        "link4mods: josephine, peter, jasper",
        "linkmods: josephine, peter, jasper",
        "link 4 mods: josephine, peter, jasper",
        "link mods: josephine, peter, jasper",
        "link4[A15]mods: josephine, peter, jasper.",
        "link 4 A15 mods josephine, peters, jasper",
        "linkmod: timmy!",
        "linkA14mod: ancient mods are the best",
        "linkscenario: scenarios are for the brave", 
        "there's a mod for that: timmy!",
        "there's an A16 mod for that: timmy!",
        "there's a scenario for that: boris?",
        "linkmod : Expanded Prosthetics",
        "linkmod :",
        "linkmod: Expanded Prosthetics",
        "linkmod:",
        "linkmod:Expanded Prosthetics",
        "linkmod :Expanded Prosthetics",
        "linkmod:Expanded Prosthetics",
        "linkmod:"
    ]:
        print("\t" + query)
        for regex in REGEXES:
            for match in regex['regex'].findall( query ):
                print("\t\t", match)
                for request in ModRequest.fromQuery( match ):
                    print("\t\t\t", request)
                    for result in search( request ):
                        print("\t\t\t\t", result)
        input("Press Enter to continue...")

