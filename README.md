# sql-database

An SQL database in a couple of lines of code. In theory backed by a key value store. In memory only.

Supports the following queries:

* ```insert into people (people_name, age) values ('Ted', 29)```
* ```select products.price, people.people_name, items.search from items inner join people on people.id = items.people inner join products on items.search = products.name where people.people_name = 'Ted'```
* ```select * from people where people.people_name = 'Ted' and people.age = 29```
* ```select search, count(*) from items group by items.search```
* **Full text search** ```select * from items where items.search ~ 'blah & sentence'``` (and, or supported)

# About

The SQL parser is really simple and doesn't produce an AST. It would be nice if in the future future the query was parsed to an AST query plan which could then be optimized.

Currently fields are indexed in four ways:

* by column
* by row
* by search value
* by full text search index

This allows the database to fulfil where queries using a hash join.

