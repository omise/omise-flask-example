import os


class Config:
    """Basic Flask configuration.

    In theory, we could get store currency and locale from Omise
    account currency.  For example, if account currency is THB then
    locale is th_TH and store currency is THB.
    """

    OMISE_SECRET_KEY = os.environ["OMISE_SECRET_KEY"]
    OMISE_PUBLIC_KEY = os.environ["OMISE_PUBLIC_KEY"]
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    OMISE_API_VERSION = os.environ.get("OMISE_API_VERSION", "2019-05-29")
    STORE_LOCALE = os.environ.get("STORE_LOCALE", "th_TH")
    STORE_CURRENCY = os.environ.get("STORE_CURRENCY", "THB")
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    SERVER_NAME = os.environ.get("SERVER_NAME")
    # AUTO_CAPTURE defaults to True unless set to 0, false, or False
    AUTO_CAPTURE = os.environ.get("AUTO_CAPTURE") not in [0, "false", "False"]
