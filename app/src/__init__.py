import os

if os.getenv("PREFER_EVENTLET"):
    import eventlet

    if not os.getenv("DEBUGPY_RUNNING"):
        eventlet.monkey_patch()
        async_mode = "eventlet"
else:
    async_mode = "threading"

from flask import Flask
from flask_socketio import SocketIO

from .ai_session import register_ai_session_handler
from .chat import register_chat_apis
from .common.config import ConfigClass
from .main import register_main


def app_factory(debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = ConfigClass.APP_SECRET

    socket = SocketIO()
    socket.init_app(
        app,
        cors_allowed_origins="*",
        async_mode=async_mode,
    )
    register_main(app=app, socket=socket)
    register_chat_apis(app=app, socket=socket)
    register_ai_session_handler(app=app, socket=socket)

    return app, socket


application, socketio = app_factory(debug=True)
