[![Omise](https://cdn.omise.co/assets/omise.png)](https://www.omise.co/developers)

[Omise](https://www.omise.co/) is a payment service provider operating in Thailand, Japan, and Singapore.
Omise provides a set of APIs that help merchants of any size accept payments online.
Read the [documentation](https://www.omise.co/docs) and start getting paid!

# Omise &hearts; Flask

Integrate the Omise payment gateway into your Python Flask app to enable convenient payment options for your users.

[Flask](https://flask.palletsprojects.com/en/1.1.x/) is a minimal web application framework written in Python that pairs well with our Python library [omise-python](https://github.com/omise/omise-python).
While this tutorial walks through some aspects of integration with Omise, it is not meant to be a comprehensive Flask or omise-python tutorial.

If you run into any issues regarding this tool and the functionality it provides, consult the frequently asked questions in our [support documents](https://www.omise.co/support).
If you can't find an answer there, post a question in our [forum](https://forum.omise.co/c/development) or [email our support team](mailto:support@omise.co).

## Requirements

To follow along, you will need:

* An Omise account (and your `$OMISE_PUBLIC_KEY` and `$OMISE_SECRET_KEY`)
* A Python 3.7 environment

## Installation

The first step is to clone the repo:

```
git clone https://github.com/omise/omise-flask-example
```

Change to the `omise-flask-example` directory.
Installation using [Pipenv](https://pipenv.readthedocs.io/en/latest/) is supported.


```
cd omise-flask-example
pipenv install
```

## Configuration

Environment variables are a good way to prevent secret keys from leaking into your code (see [The Twelve-Factor App](https://12factor.net/)).
Use the `env.example` template to create your `.env`.

```
cp env.example .env
```

Your `.env` should now look like this:

```
export OMISE_SECRET_KEY=skey_test_xxxxxxxxxxxxxxxxxxx
export OMISE_PUBLIC_KEY=pkey_test_xxxxxxxxxxxxxxxxxxx
export OMISE_API_VERSION=2017-11-02
export FLASK_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export FLASK_ENV=development
export STORE_LOCALE=th_TH
export STORE_CURRENCY=THB
export PREFERRED_URL_SCHEME=http
export SERVER_NAME=localhost:5000
```

Replace the values for `OMISE_SECRET_KEY` and `OMISE_PUBLIC_KEY` with your keys.
They can be found on your [Omise Dashboard](https://dashboard.omise.co).
After logging in, click "Keys" in the lower-left corner.
Copy and paste them into this file.

For `FLASK_SECRET_KEY`, create a random string of characters.
How to do this is left as an [exercise for the reader](https://media.giphy.com/media/o0vwzuFwCGAFO/giphy.gif).

> The above currency and locale assume a test account registered in Thailand.
> If you are using a test account registered in Japan, you should also set `STORE_CURRENCY=JPY` and `STORE_LOCALE=ja_JP`.
> For Singapore, you should set `STORE_CURRENCY=SGD` and `STORE_LOCALE=en_SG`.

At this point, you should be able to run the app by typing the
following and hitting `ENTER`:

```
pipenv run flask run
```

The Flask app should be running at [http://localhost:5000](http://localhost:5000).
Go look at it, add some items to the cart, and hit checkout (you can use [these test credit card numbers](https://www.omise.co/api-testing) to create a test charge).

![pipenv run flask run](https://cdn.omise.co/assets/screenshots/omise-flask-example/pipenv-run-flask-run.gif)

## How Was This App Made?

The source code should be fairly minimal and (hopefully) clear.
For the rest of this `README.md`, let's walk through one way to integrate the Omise payment gateway as expressed in this basic Flask app.
We will:

- Create an *app factory*
- Define a *blueprint*
- Prepare to charge a credit card
- Successfully charge that credit card
- Use the dashboard to see our charge

This README only lists the highlights.
Please consult the source code for the full implementation.

### Build Your Factory

At the root of your `omise-flask-example` directory should be `app.py`.
`app.py` sets up the configuration for this Flask app.
It defines the [application factory](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/) `create_app` which creates the Flask app.
This factory does the following:

1. Initializes our Flask `app`
1. Configures the app using the `Config` class (loaded from `config.py`)
1. Registers blueprints (using the `register_blueprint` method) on the Flask `app`
1. Returns the created `app`

```python
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
    Talisman(
        app,
        content_security_policy={"default-src": "'unsafe-inline' 'self' *.omise.co"},
    )

    return app
```

Notice that there's not actually very much payment-related going on here.
The actual mechanics of charging a credit card are stored in the `checkout` blueprint we registered on the app above.
Blueprints help manage modular Flask applications.
From the [documentation](https://flask.palletsprojects.com/en/1.1.x/blueprints/):

> Flask uses a concept of blueprints for making application components and supporting common patterns within an application or across applications.
> Blueprints can greatly simplify how large applications work and provide a central means for Flask extensions to register operations on applications.
> A Blueprint object works similarly to a Flask application object, but it is not actually an application.
> Rather it is a blueprint of how to construct or extend an application.

In theory, you could extract these blueprints and include them in your own Omise-powered Flask app.

### Laying Out the Blueprint

On disk, the `checkout` blueprint and its template are stored in a folder called `payment` which looks like this:

```
$ tree payment
payment
├── checkout.py
└── templates
    ├── barcode.html
    ├── checkout.html
    └── complete.html
```

To create this blueprint, we make an instance of the `Blueprint` class and define a `template_folder` under the current directory.
After that, we add a route to the instance the same way we would with a normal Flask `app` instance using the [route decorator](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.route) prepending the blueprint name: `@checkout.route("/checkout")`.

```python
checkout = Blueprint("checkout", __name__, template_folder="templates")

@checkout.route("/checkout")
def check_out():
    cart = Cart()
    return render_template(
        "checkout.html",
        key=current_app.config.get("OMISE_PUBLIC_KEY"),
        cart=cart,
        Price=Price,
        currency=current_app.config.get("STORE_CURRENCY"),
        customer=session.get("customer")
    )
```

Now when the user goes to the `/checkout` route, this blueprint will handle the rendering using the template `checkout.html` passing in values for `key`, `cart`, `Price`, `currency`, and `customer`.
The template displays a very simple cart and the Omise-specific `<form>` code which powers our payment button.
Here's a minimal version of what this could look like.

```html
<form class="checkout-form" name="checkoutForm" method="POST" action="/charge">
  <script type="text/javascript" src="https://cdn.omise.co/omise.js"
          data-key="{{ key }}"
          data-amount="{{ cart.total() }}"
          data-currency="{{ currency }}">
  </script>
</form>
```

The payment form generation is handled by [Omise.js](https://www.omise.co/omise-js) which (at a minimum) accepts a `key` (your `OMISE_PUBLIC_KEY`), `amount`, and `currency`.

![Payment Pop Up](https://cdn.omise.co/assets/screenshots/omise-flask-example/payment-pop-up.gif)

Once the user clicks on the button "Pay with Omise", the form sends a `POST` request to our local `/charge` endpoint providing one of the parameters `omiseToken` (for credit cards) or `omiseSource` (for everything else).

### Getting Ready to Charge

**This part is important: We use the token to issue the charge rather than the actual credit card details.**
**Never have credit card details stored on or pass through your server.**

Using Omise, we avoid the risk of having to [collect card information](https://www.omise.co/collecting-card-information) directly.
We can retrieve token in Flask by calling `request.form.get("omiseToken")`.
So, for our `/charge` endpoint, we do to at least the following:

1. Get the cart information (to determine the price)
1. Get the `omiseToken` or `omiseSource` we need to actually issue the charge
1. Configure the `omise` object which issues the charge
1. Create an `order_id`

> The below example additionally collects `email` and `customer` to enable customer payment flows.
> See the full implementation for more detail.

We configure the `omise` object by providing the `OMISE_SECRET_KEY` and `OMISE_API_VERSION` we provided at the initial configuration of the app.
While the API version is not strictly necessary, it is good practice to set this explicitly so that we can migrate to a new version in a controlled way (see our guidelines for [API versioning](https://www.omise.co/api-versioning)).
After this, we can then create a UUID `order_id`.
This is not required by Omise, but will be useful for you as a customer-facing identifier for the order.

```python
@checkout.route("/charge", methods=["POST"])
def charge():
    cart = Cart()
    email = request.form.get("email")
    token = request.form.get("omiseToken")
    source = request.form.get("omiseSource")
    customer = request.form.get("omiseCustomer")
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")
    order_id = uuid.uuid4()
```

### Attempting the Charge

We are almost ready to issue the charge request, but we should keep in mind that there are two ways for a charge API request to go wrong.
In the first case, the request could return in an [error object](https://www.omise.co/api-errors) with an HTTP status code (e.g. `401 Authentication Failure`).
When using `omise-python`, this type of failure can be handled with a `try/except` block.
Another way the request could fail is if the charge API request returns a [charge object](https://www.omise.co/charges-api) with a `failure_code`.

#### Try/Except

To create a charge using `omise-python`, we call `omise.Charge.create` which accepts several parameters, of which `token`, `amount`, and `currency` are required.
The `amount` and `currency` are retrieved from the session cart and the configured `STORE_CURRENCY`, respectively.

Optionally, we are adding several parameters, `ip`, `description`, and `return_uri`, all of which are technically optional, but highly recommended.

* `ip` and `description` hold the customer IP and a description of the cart contents to help in Omise's automated fraud analysis.
* Since most payment methods require a redirection to an authorization service, provide `return_uri` which is the URI to which the customer must be redirected after authorization.
* We are also passing a [custom metadata parameter](https://www.omise.co/store-your-data-on-omise-with-the-metadata-api).
This object can be any shape, and I am using it to log the app that made this charge ("Omise Flask"), the current cart contents, and the `order_id` I generated above.

After creating a charge, the result is passed to a processing function (`process`) which will decide what to do next.

```python
chrg = omise.Charge.create(
    amount=cart.total(),
    currency=current_app.config.get("STORE_CURRENCY"),
    metadata={
        "app": "Omise Flask",
        "cart": {"items": cart.items()},
        "order_id": str(order_id),
    },
    return_uri=url_for("checkout.order", order_id=order_id, _external=True),
    ip=get_client_ip(),
    description=str(cart.items()),
    **nonce,
)
return process(chrg)
```

If the charge returns an error within our `try` clause, we flash a message and return to the checkout page.
I am differentiating between `omise.errors.BaseError` and more generic Python exception to make it easier to troubleshoot in the future.

```python
except omise.errors.BaseError as e:
    flash("""An error occurred.  Please contact support.""")
    current_app.logger.error(f"""OmiseError: {repr(e)}.  See https://www.omise.co/api-errors""")
    return redirect(url_for("checkout.check_out"))
except Exception as e:
    flash("""An error occurred.  Please contact support.""")
    current_app.logger.error(repr(e))
    return redirect(url_for("checkout.check_out"))
```

#### Successfully Charging

Of course, we are really here to *handle payments like a boss*.

In the `process` function, we check whether the charge meets a series of conditions which determine how to handle it.
For instance, if it requires a redirection to an authorization service, we redirect the user.

If no exception was raised, `failure_code` is null, and `charge.status` is `successful`, we have successfully charged the card!
In the case of success, we:

1. Empty the cart
1. Let the user know the charge with successful providing their Order ID
1. Return to the completed charge page

```python
if chrg.status == "successful":
    cart.empty()
    flash(f"Order {order_id} successfully completed.")
    return render_template("complete.html")
```

### Viewing the Dashboard

Check [your dashboard](https://dashboard.omise.co) to see the charge and all its associated details.

![Dashboard Details](https://cdn.omise.co/assets/screenshots/omise-flask-example/dashboard-details.png?refresh_cache)

## Get Paid

Thanks for following along.
I hope you found this walkthrough helpful.
[Omise](https://www.omise.co/) is a payment service provider operating in Thailand, Japan, and Singapore.
[omise-python](https://github.com/omise/omise-python) is just one of the many [open-source libraries for integrating Omise](https://github.com/omise/) into your app.
We also offer [plugins for popular e-commerce platforms](https://www.omise.co/plugins).

# Testing

```
pipenv install --dev
pipenv run python -m pytest --disable-pytest-warnings
```

# Contributing

Use `black` for formatting:

```
pipenv install --dev
pipenv run black --exclude venv .
```
