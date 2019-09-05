from flask import Flask
from config import Config
from store.store import store
from payment.checkout import checkout
from webhook.webhook import webhook
from flask_talisman import Talisman


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(store)
    app.register_blueprint(checkout)
    app.register_blueprint(webhook)
    csp = {"default-src": ["'unsafe-inline' 'self' '*.omise.co'"]}
    Talisman(app, content_security_policy=csp)

    return app
