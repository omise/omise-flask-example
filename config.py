import os


class Config:
    """
    Flask configuration
    """

    OMISE_SECRET_KEY = os.environ["OMISE_SECRET_KEY"]
    OMISE_PUBLIC_KEY = os.environ["OMISE_PUBLIC_KEY"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    OMISE_API_VERSION = os.environ.get("OMISE_API_VERSION", "2019-05-29")
    STORE_LOCALE = os.environ.get("STORE_LOCALE", "th_TH")
    STORE_CURRENCY = os.environ.get("STORE_CURRENCY", "THB")
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
