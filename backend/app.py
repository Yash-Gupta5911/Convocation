from flask import Flask, send_from_directory
import os

def create_app():
    app = Flask(__name__)

    # Serve FRONTEND folder as root static directory
    FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

    @app.route("/<path:filename>")
    def frontend_files(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    # Default route -> load login.html
    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "login.html")

    # Register blueprints
    from routes.register import bp as register_bp
    app.register_blueprint(register_bp)

    return app


app = create_app()
