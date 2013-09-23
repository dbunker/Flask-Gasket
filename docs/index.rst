Flask-Gasket
===========

Flask-Gasket is an extension to Flask that allows for the simple configuration of REST API using a NoSQL database. Since routing, validation, functions, and return data all revolve around the data stored in the REST API, much of this information can be consolidated in Gasket's main configuration file.

Features
--------

- Centralized configuration of routing and model information
- Support for common uses including passwords
- Easily configured to provide filtered and sorted lists of data
- Currently supports Riak as backend with planned support for Redis, MongoDB, and Cassandra
