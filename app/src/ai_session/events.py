from socket import SocketIO
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

    @socket.on("message")
    def handle_message(msg):
        print(session)
        sid = request.sid
        model.update_activity(sid)
        logging.info(f"Received from {sid}: {msg}")

        if msg == "process":
            socket.start_background_task(target=process_task, sid=sid)

    @socket.on("recognize")
    def handle_message(msg):
        print(session)
        sid = request.sid
        model.update_activity(sid)
        logging.info(f"New Request: Recognize {msg}")

        if msg == "process":
            socket.start_background_task(target=process_task, sid=sid)

    def process_task(sid):
        for i in range(1, 11):
            socket.emit("message", {"msg": f"Tick {i}"}, to=sid)
            eventlet.sleep(1)
        socket.emit("message", {"msg": "done"}, to=sid)

    @socket.on("disconnect")
    def handle_disconnect():
        print(session)
        sid = request.sid
        logging.info(f"Client disconnected: {sid}")
        model.remove_client(sid)

