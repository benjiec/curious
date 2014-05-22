Curious
=======

Curious aims to simplify some common database querying and report generation tasks. Curious queries let you quickly explore relationships among objects, search for objects using recursive relationships, and search for objects loosely connected among different databases. Curious UI provides an interactive UI to results of a query, allowing users to sort, filter, and group results, and to continue their explorations from past results.

Curious does not replace the need to write customized UIs; the Curious UI provides a quick way to generate tables joining relational data, to help users explore data without writing code. Curious also does not replace the need to write raw SQL queries for complex queries; the Curious query language offers similar capabilities as Django QuerySets: it supports simpler filtering on single and connected models, but leaves complex queries to raw SQL.

Curious works with Django models; you can use Curious to explore data created by your existing Django applications, or build Django models to shadow non-Django managed databases (e.g. fairly trivial to do this for ActiveRecord generated databases). User queries operate on models and instances, and specify model to model relationships to traverse. A relationship can be an foreign key or many to many relationship defined by the models, or registered methods that traverse across multiple models (for convenience or performance) or even databases.


Example
-------


Query Language
--------------


Configuring Curious
-------------------


Writing Customized Relationships
--------------------------------


How Curious Works
-----------------


Disadvantages
-------------


