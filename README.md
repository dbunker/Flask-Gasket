Flask-Gasket
===========

Flask-Gasket is an extension to Flask that allows for the simple configuration of REST API using a NoSQL database. Since routing, validation, functions, and return data all revolve around the data stored in the REST API, much of this information can be consolidated in Gasket's main configuration file.

Features
--------

- Centralized configuration of routing and model information
- Support for common uses including passwords
- Easily configured to provide filtered and sorted lists of data
- Currently supports Riak as backend with planned support for Redis, MongoDB, and Cassandra

Example
-------

This example creates an basic API for user signup, login, authentication, and post creation and retrieval.

1) Install `Riak` (http://docs.basho.com/riak/latest/tutorials/installation/)
2) Make sure `secondary indexes` (http://docs.basho.com/riak/1.2.1/cookbooks/Secondary-Indexes---Configuration/) are enabled by setting LevelDB in app.config
3) Run: "riak start" in terminal to start riak
4) Run: "cd example & ln -s ../flask_gasket ."
5) Run: "python start.py" which runs the Flask server on port 5600
6) In a separate terminal run: "python test.py" to test server

Documentation
-------------

Check `Docs` (https://github.com/dbunker/Flask-Gasket/blob/master/docs/index.rst) for more information on extension.
