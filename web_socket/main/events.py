from socket import SocketIO
from flask import request, session
from flask_socketio import emit, join_room, leave_room
import logging
import eventlet

from .session_manager import ClientManager
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

    # For chats    
    @socketio.on('joined', namespace='/chat')
    def joined(message):
        """Sent by clients when they enter a room.
        A status message is broadcast to all people in the room."""
        print(session)
        room = session.get('room')
        join_room(room)
        emit('status', {
            'msg': f"{session.get('name')} has entered the room.",
        }, to=room)

    @socketio.on('text', namespace='/chat')
    def text(message):
        """Sent by a client when the user entered a new message.
        The message is sent to all people in the room."""
        print(session)
        room = session.get('room')
        items = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})) # Exclude default methods if desired
            items.append (f"Endpoint: {rule.endpoint}, Methods: {methods}, Rule: {rule}")
        msg = ",".join(items)
        print (msg)
        msg = f"{message['msg']}\n{msg}"
        emit('message', {
            'msg': f"{session.get('name')}: {msg}",
        }, to=room)



    

    @socketio.on('left', namespace='/chat')
    def left(message):
        """Sent by clients when they leave a room.
        A status message is broadcast to all people in the room."""
        print(session)
        room = session.get('room')
        leave_room(room)
        emit('status', {
            'msg': f"{session.get('name')} has left the room.",
        }, to=room)

