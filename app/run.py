import logging

from src import application, socketio

logging.getLogger("werkzeug").setLevel(logging.ERROR)

if __name__ == "__main__":
    socketio.run(application, host="0.0.0.0", port=5002)
