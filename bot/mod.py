import re

from common import EPSILON, STEAM

class Mod:
    VERSION_REGEX = re.compile(r"\[?([ab]?\d{2}|v?1\.\d)\]?", re.IGNORECASE) # https://regex101.com/r/ICiCxq/2

    def __init__(self, mod, query):
        self.title = mod['title']
        self.url = mod['url']
        self.author = mod['author']
        self.profile = mod['profile']
        self.alpha = tagsToAlpha(query.tags)
                
    def __repr__(self):
        return "[{}] {} by {} ({}, {})".format(self.alpha, self.title, self.author, self.url, self.profile) 
    
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
            "author": self.author,
            "authorUrl": self.profile
        }
    
def tagsToAlpha(tags):
    # we get Mod/Scenario, and a version tag.
    # Just loop over tags and return the first one that doesn't raise a ValueError...
    for tag in tags:
        try:
            tag = float(tag)
            if tag >= 1 - EPSILON:
                return str(tag)
            if tag >= 0.18 - EPSILON:
                return 'B{:.0f}'.format(tag*100)
            return 'A{:.0f}'.format(tag*100)
        except ValueError:
            continue