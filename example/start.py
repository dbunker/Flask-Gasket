import view
import flask_gasket.control
import flask_gasket.route
from flask import Response
import flask_gasket.doc

flask_gasket.doc.writeDoc('')
app = flask_gasket.route.getApp()

config = flask_gasket.control.loadJsonFile('config.json')
flask_gasket.route.startApp(config,view)

