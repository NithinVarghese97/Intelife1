from flask import Flask

def create_app(config_class=None):
    app = Flask(__name__, static_folder='static')
    
    # Load the configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        from config import Config
        app.config.from_object(Config)
    
    with app.app_context():
        from app import routes
    
    return app
