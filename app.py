from flask import Flask
from config import Config
from store.store import store
from payment.checkout import checkout
from webhook.webhook import webhook


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(store)
    app.register_blueprint(checkout)
    app.register_blueprint(webhook)

    return app
