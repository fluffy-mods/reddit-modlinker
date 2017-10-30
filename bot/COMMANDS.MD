Teddy is a bot, so his vocabulary is a bit limited. I've managed to teach him commands for the following;

 - [x] [Link a single mod or scenario](#link-a-single-mod-or-scenario)  
 - [x] [Link multiple mods or scenarios](#link-multiple-mods-or-scenarios)  
 - [x] [Link multiple results for a mod or scenario](#link-multiple-results-for-a-mod-or-scenario)  
 - [x] [Link to a mod or scenario for a specific Alpha of RimWorld](#link-to-a-mod-or-scenario-for-a-specific-alpha-of-rimworld)

# Link a single mod or scenario
```
there's a mod for that: [query]  
there's a scenario for that: [query]  
linkmod: [query]  
linkscenario: [query]  
```
Tells teddy to go search for `[query]`, and post a single link for the top mod/scenario for the latest version of RimWorld. 

>_note; the square brackets are just to show this is a variable, don't type them in the actual post!_

# Link multiple mods or scenarios
```
there's mods for that: [query1], [query2], ...  
there are mods for that: [query1], [query2], ...  
linkmods: [query1], [query2], ...  
there's scenarios for that: [query1], [query2], ...  
there are scenarios for that: [query1], [query2], ...  
linkscenarios: [query1], [query2], ...  
```
Asks Teddy to go and fetch a single link for each of the queries, for the latest version of RimWorld. 

>_note; there's no limit to the amount of queries you can do at once, and Teddy will even spread his response over multiple comments if necessary. Please respect reddiquete and subreddit rules. Spamming by bot may get you (and Teddy!) banned._

# Link multiple results for a mod or scenario
```
there's [count] mods for that: [query], [query], ...  
there are [count] mods for that: [query1], [query2], ...  
link[count]mods: [query1], [query2], ...  
there's [count] scenarios for that: [query], [query], ...  
there are [count] scenarios for that: [query1], [query2], ...  
link[count]scenarios: [query1], [query2], ...  
```
Asks Teddy to go and fetch `[count]` links for each of the queries, for the latest version of RimWorld. Teddy only fetches a maximum of 10 links per request. He says it's because of union rules, but I suspect he's just growing lazy. 

# Link to a mod or scenario for a specific Alpha of RimWorld 
```
there's an Alpha [alpha] mod for that: [query]  
there are [count] A[alpha] mods for that: [query1], [query2], ...  
link[A[alpha]]mod: [query]  
link alpha 16 mods: [query1, query2], ...  
```
Specifying the alpha will make Teddy search for mods/scenarios for a specific version of RimWorld.

>_note; if the alpha is not mentioned, Teddy will always search for mods/scenarios for the current version of RimWorld._  

>_note; the alpha can be provided in any common format; `A15`, `Alpha 15`, `[A15]` and `aLpHa 15` are all equivalent._

