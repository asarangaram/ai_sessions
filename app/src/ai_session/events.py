from flask_socketio import SocketIO
from flask import request, session
import logging
import eventlet

from .model import AISessionManager

logging.basicConfig(level=logging.INFO)


def register_ai_session_events(*, socket: SocketIO, model: AISessionManager):
    @socket.on("connect")
    def handle_connect():
        print(session)
        sid = request.sid
        model.create_session(sid)
        logging.info(f"Client connected: {sid}")

    @socket.on("recognize")
    def handle_message(msg):
        print(session)
        sid = request.sid
        model.update_activity(sid)
        logging.info(f"Recognize {msg}: received")
        if model.recognize(sid=sid, identifier=msg):
            logging.info(f"Recognize {msg}: succeeded")
        else:
            logging.info(f"Recognize {msg}: failed")
            

    @socket.on("disconnect")
    def handle_disconnect():
        print(session)
        sid = request.sid
        logging.info(f"Client disconnected: {sid}")
        model.remove_client(sid)

