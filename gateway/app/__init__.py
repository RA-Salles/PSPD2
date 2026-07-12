from flask import Flask
from flask_cors import CORS
from app.config import Config
from prometheus_flask_exporter import PrometheusMetrics

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    PrometheusMetrics(app)

    # Enable CORS for frontend integration
    CORS(
        app,
        origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "https://kiriland.unb.br",
        ],
        supports_credentials=True,
    )

    # Register blueprints
    #from app.auth.routes import auth_bp
    from app.api.routes import api_bp

    #app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "healthy"}

    return app
