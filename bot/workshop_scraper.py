import logging
import os
import re
import sys

from common import EPSILON, STEAM
from mod import Mod
from commands import ModRequest
from contextlib import closing
from requests import get, RequestException
from bs4 import BeautifulSoup as bs

log = logging.getLogger(__name__)

def search(query, count=1, tags=[]):
    # start with a copy of the default parameters (really just appid and search option).
    params = STEAM['WORKSHOP']['PARAMS'].copy()
    try:
        params['search_text'] = query.query
        params['numperpage'] = query.count
        params['requiredtags'] = query.tags
    except AttributeError:
        params['search_text'] = query
        params['numperpage'] = count
        params['requiredtags'] = tags
        query = ModRequest(True, query, "1.0", count)

    # fetch matching mods (using a plain html request, since the API blows balls)
    raw = fetch(query)

    # scrape information from the response and instantiate mods
    mods = [Mod(mod, query) for mod in scrape(raw)]

    # return x mods
    return mods[0:query.count]

def fetch(query: ModRequest):
    url = query.get_url()
    try:
        log.info('Fetching %s...', url)
        with get(url) as response:
            try:
                if (response.status_code == 200
                        and response.headers['Content-Type'] is not None
                        and response.headers['Content-Type'].lower().find('html') > -1):
                    return response.content
            except Exception as exc:
                log.exception(exc)
                return None
            finally:
                response.close()

    except RequestException as exc:
        log.exception(exc)
        return None

def scrape(html: str):
    mods = []
    try:
        soup = bs(html, features="html.parser")
        for _mod in soup.select("div.workshopItem"):
            title_ele = _mod.select_one("div.workshopItemTitle")
            author_ele = _mod.select_one("div.workshopItemAuthorName")
            mod = dict(
                title=title_ele.string, 
                url=title_ele.parent['href'],
                author=author_ele.a.string,
                profile=author_ele.a['href'])
            mods.append(mod)

    except Exception as exc:
        log.exception(exc)

    finally:
        return mods

if __name__ == '__main__':
    logging.basicConfig(format='%(module)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    if len(sys.argv) > 1:
        request = ModRequest(True, sys.argv[1], "1.0", 5)
        print(str(request))
        for result in search(request):
            print("\t", result)
    else:
        print("testing steam API")
        mods = search("Pawns are Capable!", 10)
        if mods is not None:
            for mod in mods:
                print("\t" + str(mod))

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
            "linkmod:",
            "there are 10 v1.0 mods for that: some text.",
            "there are 1.0 mods for that: some more text.",
            "there are version 2.0 scenarios for that: probably not",
            "link 1.0 mod: awesome sauce!",
            "link v2.2 mod: totes!",
            "there's a 1.0 mod for that: Peter",
            "there's a v1.0 mod for that: Bossman.",
            "there's a version 1.0 mod for that: Peter",
            "some text (oh by the way, there's a mod for that: Stuff) some more text",
            "link 4 v1.0 mods: peter",
            "link 1.0 mods: tommy!",
            "linkB18mods: tommy!",
            "link12B18mods: tommies",
            "there are multiple requests in this post. link20mods: fluffierthanthou. link20v1.0mods: mod"
        ]:
            print("\t" + query)
            for request in ModRequest.fromPost( query ):
                print('\t\t{!s}'.format( request ))
                for result in search(request):
                    print("\t\t\t", result)
            input("Press Enter to continue...")
    print("bye!")