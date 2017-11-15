const express = require('express');
const router = express.Router();

let links = {
    Mods: "/mods",
    Authors: "/authors",
    Linkers: "/linkers"
}

router.get('/', function( req, res, next){
    Promise.all([
        req.db.topMods( 20, false ).then( mods => {
            return {
                names: mods.map( mod => mod._id ),
                counts: mods.map( mod => mod.count )
            }
        }),
        req.db.count(),
        req.db.latestLinks( 20 )
    ]).then( resources => {
            res.render( "index", { 
                links: links,
                title: "Teddy :: Mod linking bot",
                mods: resources[0],
                count: resources[1], 
                posts: resources[2],
                moment: require('moment')
            })
        }) 
})

router.get('/mods', function(req, res, next) {
    Promise.all([
        req.db.topMods( 500 ),
        req.db.count()
    ])
        .then( results => res.render( "table", { table: results[0], count: results[1], links: links, active: "Mods", title: "Teddy :: Top mods" } ))
        .catch( err => res.render( "error", {error: err} ) )
})

router.get('/authors', function(req, res, next) {
    Promise.all([
        req.db.topAuthors( 500 ),
        req.db.count()
    ])
        .then( results => res.render( "table", { table: results[0], count: results[1], links: links, active: "Authors", title: "Teddy :: Top authors"  } ))
        .catch( err => res.render( "error", {error: err} ) )
})

router.get('/linkers', function(req, res, next) {
    Promise.all([
        req.db.topRequesters( 500 ),
        req.db.count()
    ])
        .then( results => res.render( "table", { table: results[0], count: results[1], links: links, active: "Linkers", title: "Teddy :: Top linkers"  } ))
        .catch( err => res.render( "error", {error: err} ) )
})

module.exports = router;
