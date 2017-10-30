const MongoClient = require('mongodb').MongoClient
const mongo_uri = process.env['MONGO_URI'].replace( /(^"|"$)/g, "" )

function DB() {
    this.db = null;
}

DB.prototype.connect = function( callback ){
    // connection already established
    if (this.db)
        return callback()

    // create connection
    MongoClient.connect( mongo_uri, (err, database) => {
        if (err) {
          console.error( "Database connection failed" )
          console.error( JSON.stringify( err, null, 4 ) );
          process.exit( 1 );
        } 
        console.log( "Database connected" );
        this.db = database;
        callback();
    })
}

DB.prototype.count = function(){
    return this.db.collection( "requests_collection" ).count();
}

DB.prototype.topMods = function( limit = 10, table = true ){
    return this.db.collection( "requests_collection" ).aggregate([
        {
            $group: {
              _id: "$mod.title",
              count: { $sum: 1 },
              url: { $first: "$mod.url" },
              author: { $first: "$mod.author" },
            }
        }, 
        { 
           $sort: { count: -1 }
        },
        {
            $limit: limit
        }
    ]).toArray()
      .then( docs => {
            if (table){
                let table = {
                    title: "Mods",
                    order: '[[ 2, "desc" ]]',
                    columns: [
                        { title: "Mod", width: "50%" },
                        { title: "Author", width: "30%" },
                        { title: "Count", width: "20%" }
                    ],
                    rows: []
                }  
                for ( let row of docs )
                    table.rows.push( [ row._id, row.author, row.count ]);
                return table;
            } else {
                return docs;
            }
      })
}

DB.prototype.topAuthors = function( limit = 10, table = true ){
    return this.db.collection( "requests_collection" ).aggregate([
        {
            $group: {
              _id: "$mod.author",
              count: { $sum: 1 },
              url: { $first: "$mod.authorUrl" },
            }
        }, 
        { 
           $sort: { count: -1 }
        },
        {
            $limit: limit
        }
    ]).toArray()
        .then( docs => {
          if (table){
              let table = {
                  title: "Authors",
                  order: '[[ 1, "desc" ]]',
                  columns: [
                      { title: "Author", width: "80%" },
                      { title: "Count", width: "20%" }
                  ],
                  rows: []
              }  
              for ( let row of docs )
                  table.rows.push( [ row._id, row.count ]);
              return table;
          } else {
              return docs;
          }
    })
}

DB.prototype.topRequesters = function( limit = 10, table = true ){
    return this.db.collection( "requests_collection" ).aggregate([
        {
            $group: {
              _id: "$requestingRedditor",
              count: { $sum: 1 }
            }
        }, 
        { 
           $sort: { count: -1 }
        },
        {
            $limit: limit
        }
    ]).toArray()
        .then( docs => {
        if (table){
            let table = {
                title: "Linkers",
                order: '[[ 1, "desc" ]]',
                columns: [
                    { title: "Redditor", width: "80%" },
                    { title: "Count", width: "20%" }
                ],
                rows: []
            }  
            for ( let row of docs )
                table.rows.push( [ row._id, row.count ]);
            return table;
        } else {
            return docs;
        }
    })
}

module.exports = DB;