import eventlet

eventlet.monkey_patch()

from flask_socketio import SocketIO
from flask import Flask

from .common.config import ConfigClass
from .chat import register_chat_apis
from .ai_session import register_ai_session_handler
from .main import register_main

def app_factory(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = ConfigClass.APP_SECRET

    socket = SocketIO()
    socket.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
    )
    register_main(app=app, socket=socket)
    register_chat_apis(app=app, socket=socket)
    register_ai_session_handler(app=app, socket=socket)

    return app, socket


application, socketio = app_factory(debug=True)



    