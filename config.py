import os


class Config(object):
    OMISE_SECRET_KEY = os.environ["OMISE_SECRET_KEY"]
    OMISE_PUBLIC_KEY = os.environ["OMISE_PUBLIC_KEY"]
    OMISE_API_VERSION = os.environ["OMISE_API_VERSION"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    STORE_LOCALE = os.environ["STORE_LOCALE"] or "th_TH"
    STORE_CURRENCY = os.environ["STORE_CURRENCY"] or "THB"
