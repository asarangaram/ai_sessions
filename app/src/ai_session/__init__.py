from flask import  Flask
from flask_smorest import Blueprint

from .model import AISessionManager
from .events import register_ai_session_events
from .resources import register_sessions_resources
from flask_socketio import SocketIO


def register_ai_session_handler(*, app: Flask, socket: SocketIO):
    model = AISessionManager()
    bp = Blueprint("aisession", __name__, url_prefix="/sessions")

    register_sessions_resources(bp=bp, model=model)
    register_ai_session_events(socket=socket, model=model)
    app.register_blueprint(bp)
    pass
