import os
import psutil
from flask import request, session
from flask_socketio import SocketIO
from loguru import logger

from .model import AISessionManager


def register_ai_session_events(*, socket: SocketIO, model: AISessionManager):
    def getMemory():
        return psutil.Process(os.getpid()).memory_info().rss / 1024**2, "MB"

    @socket.on("connect")
    def handle_connect():
        sid = request.sid
        model.create_session(sid)
        logger.info(f"Client connected: {sid}")

    @socket.on("recognize")
    def handle_message(msg):
        sid = request.sid
        model.update_activity(sid)
        logger.info(f"Recognize {msg}: received")
        if model.recognize(sid=sid, identifier=msg):
            logger.info(f"Recognize {msg}: succeeded")
        else:
            logger.info(f"Recognize {msg}: failed")
        logger.info(f"Memory: {getMemory()}")

    @socket.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        logger.info(f"Client disconnected: {sid}")
        model.remove_client(sid)
