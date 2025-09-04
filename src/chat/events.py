from flask import session
from flask_socketio import emit, join_room, leave_room
from socket import SocketIO


def register_chat_events(socketio: SocketIO,  app=None):
    @socketio.on("joined", namespace="/chat")
    def joined(message):
        """Sent by clients when they enter a room.
        A status message is broadcast to all people in the room."""
        print(session)
        room = session.get("room")
        join_room(room)
        emit(
            "status",
            {
                "msg": f"{session.get('name')} has entered the room.",
            },
            to=room,
        )

    @socketio.on("text", namespace="/chat")
    def text(message):
        """Sent by a client when the user entered a new message.
        The message is sent to all people in the room."""
        print(session)
        room = session.get("room")
        msg = message['msg']
        emit(
            "message",
            {
                "msg": f"{session.get('name')}: {msg}",
            },
            to=room,
        )

    @socketio.on("left", namespace="/chat")
    def left(message):
        """Sent by clients when they leave a room.
        A status message is broadcast to all people in the room."""
        print(session)
        room = session.get("room")
        leave_room(room)
        emit(
            "status",
            {
                "msg": f"{session.get('name')} has left the room.",
            },
            to=room,
        )