#!/bin/env python

import eventlet

eventlet.monkey_patch()


from web_socket import create_app, socketio

application = create_app(debug=True)

socketio.init_app(
    application,
    cors_allowed_origins="*",
    async_mode="eventlet",
)

if __name__ == "__main__":
    socketio.run(application, host="0.0.0.0", port=5000)
