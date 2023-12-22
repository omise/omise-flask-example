[![Opn Payments](https://www.opn.ooo/assets/svg/logo-opn-full.svg)](https://www.opn.ooo)

[Opn Payments](https://www.opn.ooo/) is a payment service provider operating in Thailand, Japan, and Singapore.
Opn Payments provides a set of APIs that help merchants of any size accept payments online.
Read the [documentation](https://docs.opn.ooo/) and start getting paid!

# Omise &hearts; Flask

Integrate the Opn payment gateway into your Python Flask application to enable convenient payment options for your users.

[Flask](https://flask.palletsprojects.com/en/1.1.x/) is a minimal web application framework written in Python that pairs well with our Python library [omise-python](https://github.com/omise/omise-python).

While this tutorial walks through some aspects of integration with Opn Payments, it is not meant to be a comprehensive Flask or omise-python tutorial.

If you run into any issues regarding this tool and the functionality it provides, consult the frequently asked questions in our [support documents](https://www.omise.co/support).
If you can't find an answer there, [email our support team](mailto:support@opn.ooo).

## Requirements

To follow along, you will need:

* An Opn Payments account (and your `$OMISE_PUBLIC_KEY` and `$OMISE_SECRET_KEY`)
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
export AUTO_CAPTURE=False
```

Replace the values for `OMISE_SECRET_KEY` and `OMISE_PUBLIC_KEY` with your keys.
They can be found on your [Opn Payments Dashboard](https://dashboard.omise.co).
After logging in, click "Keys" in the lower-left corner.
Copy and paste them into this file.

For `FLASK_SECRET_KEY`, create a random string of characters.
How to do this is left as an [exercise for the reader](https://media.giphy.com/media/o0vwzuFwCGAFO/giphy.gif).

With `AUTO_CAPTURE`, we have set it to `False` to delay capture and only pre-authorize card charges.

> The currency and locale mentioned in the `.env` file assume a test account registered in Thailand.
> If you are using a test account registered in Japan, you should also set `STORE_CURRENCY=JPY` and `STORE_LOCALE=ja_JP`.
> For Singapore, you should set `STORE_CURRENCY=SGD` and `STORE_LOCALE=en_SG`.

At this point, you should be able to run the application using the following command:

```
pipenv run flask run
```

The Flask application should be running at [http://localhost.localdomain:5000](http://localhost.localdomain:5000).
Go look at it, add some items to the cart, and hit checkout (you can use [these test credit card numbers](https://docs.opn.ooo/api-testing) to create a test charge).

![pipenv run flask run](https://cdn.omise.co/assets/screenshots/omise-flask-example/pipenv-run-flask-run.gif)

## How was this application made?

The source code should be fairly minimal and (hopefully) clear.
For the rest of this `README.md`, let's walk through a way to integrate the Opn payment gateway as expressed in this basic Flask application.
We will:

- Create an *app factory*
- Define a *blueprint*
- Prepare to charge a card
- Successfully charge that card
- Use the dashboard to see our charge

This README lists the highlights.
Please consult the source code for the full implementation.

### Build your factory

At the root of your `omise-flask-example` directory should be `app.py`.
`app.py` sets up the configuration for this Flask application.
It defines the [application factory](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/) `create_app` that creates the Flask application.
This factory does the following:

1. Initializes our Flask `app`
1. Configures the application using the `Config` class (loaded from `config.py`)
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

Notice that there is not much of payment-related activity happening here.
The actual mechanics of charging a card are stored in the `checkout` blueprint we registered on the application previously.
Blueprints help manage modular Flask applications.
From the [documentation](https://flask.palletsprojects.com/en/1.1.x/blueprints/):

> Flask uses a concept of blueprints for making application components and supporting common patterns within an application or across applications.
> Blueprints can greatly simplify how large applications work and provide a central means for Flask extensions to register operations on applications.
> A Blueprint object works similarly to a Flask application object, but it is not actually an application.
> Rather, it is a blueprint of how to construct or extend an application.

In theory, you could extract these blueprints and include them in your own Opn-powered Flask application.

### Laying out the blueprint

On disk, the `checkout` blueprint and its template are stored in a folder called `payment` that resembles:

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
The template displays a very simple cart and the Opn-specific `<form>` code that powers our payment button.
Here's a minimal version of how this would look.

```html
<form class="checkout-form" name="checkoutForm" method="POST" action="/charge">
  <script type="text/javascript" src="https://cdn.omise.co/omise.js"
          data-key="{{ key }}"
          data-amount="{{ cart.total() }}"
          data-currency="{{ currency }}">
  </script>
</form>
```

The payment form generation is handled by [Omise.js](https://docs.opn.ooo/omise-js), which (at a minimum) accepts a `key` (your `OMISE_PUBLIC_KEY`), `amount`, and `currency`.

![Payment Pop Up](https://cdn.omise.co/assets/screenshots/omise-flask-example/payment-pop-up.gif)

Once the user clicks the button "Pay with Opn Payments", the form sends a `POST` request to our local `/charge` endpoint providing one of the parameters `omiseToken` (for  cards) or `omiseSource` (for everything else).

### Getting ready to charge

**This part is important: We use the token to issue the charge rather than the actual card details.**
**Never have card details stored on or pass through your server.**

Using Opn Payments, we avoid the risk of having to [collect card information](https://docs.opn.ooo/collecting-card-information) directly.
We can retrieve a token in Flask by calling `request.form.get("omiseToken")`.
So, for our `/charge` endpoint, we do to at least the following:

1. Get the cart information (to determine the price)
1. Get the `omiseToken` or `omiseSource` for which we need to actually issue the charge
1. Configure the `omise` object that issues the charge
1. Create an `order_id`

> The following example additionally collects `email` and `customer` to enable customer payment flows.
> See the full implementation for more details.

We configure the `omise` object by providing the `OMISE_SECRET_KEY` and `OMISE_API_VERSION` that we provided during the initial configuration of the application.
While the API version is not strictly necessary, it is a good practice to set this explicitly so that we can migrate to a new version in a controlled way (see our guidelines for [API versioning](https://docs.opn.ooo/api-versioning)).
After this, we can then create a UUID `order_id`.
This is not required by Opn Payments, but will be useful for you as a customer-facing identifier for the order.

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

### Attempting the charge

We are almost ready to issue the charge request, but we should keep in mind that there are two ways for a charge API request to go wrong.
First, the request could return an [error object](https://docs.opn.ooo/api-errors) with a HTTP status code (e.g. `401 Authentication Failure`).
When using `omise-python`, this type of failure can be handled with a `try/except` block.
Another way the request could fail is if the charge API request returns a [charge object](https://docs.opn.ooo/charges-api) with a `failure_code`.

#### Try/Except

To create a charge using `omise-python`, we call `omise.Charge.create` that accepts several parameters, of which `token`, `amount`, and `currency` are required.
The `amount` and `currency` are retrieved from the session cart and the configured `STORE_CURRENCY`, respectively.

Optionally, we are adding several parameters, `ip`, `description`, and `return_uri`, all of which are technically optional, but highly recommended.

* `ip` and `description` hold the customer IP and a description of the cart contents to help in Opn Payments' automated fraud analysis.
* Since most payment methods require a redirection to an authorization service, provide `return_uri`, which is the URI to which the customer must be redirected after authorization.
* We are also passing a [custom metadata parameter](https://www.omise.co/store-your-data-on-omise-with-the-metadata-api).
This object can be of any form, and we are using it to log the application that made this charge ("Omise Flask"), the current cart contents, and the `order_id` generated previously.

After creating a charge, the result is passed to a processing function (`process`) that will decide what to do next.

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
We are differentiating between `omise.errors.BaseError` and the more generic Python exception to make it easier to troubleshoot in the future.

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

#### Successfully charging

Of course, we are really here to *handle payments like a boss*.

In the `process` function, we check whether the charge meets a series of conditions that determine how to handle it.
For instance, if it requires a redirection to an authorization service, we redirect the user.

If no exception was raised, `failure_code` is null, and `charge.status` is `successful`, we have successfully charged the card!
In the case of success, we:

1. Empty the cart
1. Let the user know the charge is successful and provide their Order ID
1. Return to the completed charge page

```python
if chrg.status == "successful":
    cart.empty()
    flash(f"Order {order_id} successfully completed.")
    return render_template("complete.html")
```

### Viewing the dashboard

Check [your dashboard](https://dashboard.omise.co) to see the charge and all its associated details.

![Dashboard Details](https://cdn.omise.co/assets/screenshots/omise-flask-example/dashboard-details.png?refresh_cache)

## Get paid

Thanks for following along.
We hope you found this walkthrough helpful.
[Opn Payments](https://www.opn.ooo) is a payment service provider operating in Thailand, Japan, and Singapore.
[omise-python](https://github.com/omise/omise-python) is just one of the many [open-source libraries for integrating Opn Payments](https://github.com/omise/) into your application.
We also offer [plugins for popular e-commerce platforms](https://docs.opn.ooo/integrations).

[Sign up](https://dashboard.omise.co/signup)!

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
