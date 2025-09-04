from socket import SocketIO
from flask import request, session
import logging
import eventlet

from .manager import ClientManager

logging.basicConfig(level=logging.INFO)


def register_events(socketio: SocketIO, clients: ClientManager, app=None):
    @socketio.on("connect")
    def handle_connect():
        print(session)
        sid = request.sid
        clients.create_session(sid)
        logging.info(f"Client connected: {sid}")

    @socketio.on("message")
    def handle_message(msg):
        print(session)
        sid = request.sid
        clients.update_activity(sid)
        logging.info(f"Received from {sid}: {msg}")

        if msg == "process":
            socketio.start_background_task(target=process_task, sid=sid)

    @socketio.on("recognize")
    def handle_message(msg):
        print(session)
        sid = request.sid
        clients.update_activity(sid)
        logging.info(f"New Request: Recognize {msg}")

        if msg == "process":
            socketio.start_background_task(target=process_task, sid=sid)

    def process_task(sid):
        for i in range(1, 11):
            socketio.emit("message", {"msg": f"Tick {i}"}, to=sid)
            eventlet.sleep(1)
        socketio.emit("message", {"msg": "done"}, to=sid)

    @socketio.on("disconnect")
    def handle_disconnect():
        print(session)
        sid = request.sid
        logging.info(f"Client disconnected: {sid}")
        clients.remove_client(sid)

