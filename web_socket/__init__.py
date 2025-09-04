from flask import  Flask
from flask_socketio import SocketIO
from flask_smorest import Blueprint
from .main.session_manager import ClientManager


from .main.events import register_events
from .main.routes import register_routes
from .main.resources import register_sessions_resources


def app_factory( debug=False, socketio=None):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "gjr39dkjn344_!67#"

    clients=ClientManager()
    main_bp = Blueprint('main', __name__)
    register_sessions_resources(main_bp, clients)
    register_routes(main_bp)
    app.register_blueprint(main_bp)
    
    
    if not socketio:
        socketio = SocketIO()

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
    )
    
    register_events(socketio, clients, app)
    
    return app, socketio
