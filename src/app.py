import eventlet

eventlet.monkey_patch()

from flask_socketio import SocketIO
from flask import Flask

from src.chat import register_chat_apis
from src.ai_session import register_ai_session_handler


def app_factory(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "gjr39dkjn344_!67#"

    socket = SocketIO()
    socket.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
    )

    register_chat_apis(app=app, socket=socket)
    register_ai_session_handler(app=app, socket=socket)

    return app, socket


application, socketio = app_factory(debug=True)


if __name__ == "__main__":
    socketio.run(application, host="0.0.0.0", port=5003)
