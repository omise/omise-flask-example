from flask import Flask
from config import Config
from store.store import store
from payment.checkout import checkout


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(store)
    app.register_blueprint(checkout)

    return app
