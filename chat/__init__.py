#!/bin/env python
import eventlet

eventlet.monkey_patch()

from web_socket import app_factory
application, socketio = app_factory(debug=True)

