from flask import Flask
from flask_smorest import Blueprint
from flask_socketio import SocketIO

from .events import register_chat_events
from .routes import register_chat_routes


def register_chat_apis(*, app: Flask, socket: SocketIO):
    main_bp = Blueprint("chat", __name__, url_prefix="/chat")

    register_chat_routes(main_bp)
    app.register_blueprint(main_bp)

    register_chat_events(socket, app)
    pass
