# sql-database

An SQL database in a couple of lines of code. In theory backed by a key value store. In memory only.

# About

The SQL parser is really simple and doesn't produce an AST. It would be nice if in the future future the query was parsed to an AST query plan which could then be optimized.

Currently fields are indexed in three ways:

* by column
* by row
* by search value

This allows the database to fulfil where queries using as hash join.

