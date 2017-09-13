# RimWorld Mod Linker
This is the home of Teddy. Teddy is a helpful bot who frequents a number of RimWorld related reddits, and after a few seconds, he'll come back and post links to the mods he found. Hopefully that will be the mods you were looking for. Helpfully, he'll also post a link to the search results he found, so you can always pick up where Teddy left off.

Teddy is heavily inspired by the [FactorioModPortalBot](https://github.com/michael-3-141/FactorioModPortalBot/) by [/u/michael________](https://www.reddit.com/u/michael________), and the Python For Engineers [Build a Reddit Bot](http://pythonforengineers.com/build-a-reddit-bot-part-1/) articles. Teddy wouldn't have been quite such a joy to make without [PRAW](https://github.com/praw-dev/praw).

## Where can I find Teddy?
Teddy frequents these reddits;
 - [/r/RimWorld](https://reddit.com/r/RimWorld)
 - [/r/TalesFromRimWorld](https://reddit.com/r/TalesFromRimWorld)
 - [/r/ShitRimWorldSays](https://reddit.com/r/ShitRimWorldSays)
 - [/r/SpaceCannibalism](https://reddit.com/r/SpaceCannibalism)

## How do I ask Teddy to fetch me a link?
Teddy is a bot, so his vocabulary is a bit limited. I've managed to teach him the following commands;

`there's a mod for that: [query]`  
`there's a scenario for that: [query]`  
`linkmod: [query]`  
`linkscenario: [query]`  
Tells teddy to go search for `[query]`, and post a single link for the top mod/scenario. 

>_note; the square brackets are just to show this is a variable, don't type them in the actual post!_

`there's mods for that: [query1], [query2], ...`  
`there are mods for that: [query1], [query2], ...`  
`linkmods: [query1], [query2], ...`  
`there's scenarios for that: [query1], [query2], ...`  
`there are scenarios for that: [query1], [query2], ...`  
`linkscenarios: [query1], [query2], ...`  
Asks Teddy to go and fetch a single link for each of the queries. 

>_note; there's no limit to the amount of queries you can do at once, and Teddy will even spread his response over multiple comments if necessary. Please respect reddiquete and subreddit rules. Spamming by bot may get you (and Teddy!) banned._

`there's [count] mods for that: [query], [query], ...`  
`there are [count] mods for that: [query1], [query2], ...`  
`link[count]mods: [query1], [query2], ...`  
`there's [count] scenarios for that: [query], [query], ...`  
`there are [count] scenarios for that: [query1], [query2], ...`  
`link[count]scenarios: [query1], [query2], ...`  
Asks Teddy to go and fetch `[count]` links for each of the queries. Teddy only fetches a maximum of 10 links per request. He says it's because of union rules, but I suspect he's just growing lazy. 

## How can I help make Teddy better?
You can leave suggestions, bug reports and other correspondence for Teddy [here](/issues). 

If you're half-decent with python (2.7*), have a good idea, and are willing to spend the time to code it out and create a pull request, I'll be more than happy to accept it.

Teddy drinks a lot of coffee, enjoys the occasional whisky and  his girlfriend could murder salty caramel fudge. If you're feeling so inclined, you could help me keep a nice stock of the above mentioned goodies...

[![Buy Me a Coffee](http://i.imgur.com/EjWiUwx.gif)](https://ko-fi.com/fluffymods)

*: Why not 3, you ask? Well, because I didn't realise I only had 2.7 installed locally, and wouldn't really know the difference between 2 and 3 if it hit me in the face. I just fix them syntax errors until it (mostly) does what I want.