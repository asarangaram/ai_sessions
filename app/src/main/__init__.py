


from socket import SocketIO
from flask import Flask
from flask_smorest import Blueprint
from .resources import register_main_resources

def register_main(*, app: Flask, socket: SocketIO):
    bp = Blueprint("main", __name__, )
    register_main_resources(bp=bp)
    app.register_blueprint(bp)
    pass