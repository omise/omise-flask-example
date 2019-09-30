[![Omise](https://cdn.omise.co/assets/omise.png)](https://www.omise.co/developers)

[Omise](https://www.omise.co/) is a payment service provider operating in Thailand, Japan, and Singapore.
Omise provides a set of APIs that help merchants of any size accept payments online.
Read the [documentation](https://www.omise.co/docs) and start getting paid!

# Omise &hearts; Flask

Omise enables modern payments.
Integrate the Omise payment gateway into your Python Flask app to enable a convenient payment option for your users.

[Flask](http://flask.pocoo.org/) is a minimal web application framework written in Python that pairs well with our Python library [omise-python](https://github.com/omise/omise-python).
While this tutorial walks through some aspects of integration with Omise, it is not meant to be a comprehensive [Flask](http://flask.pocoo.org/) or [omise-python](https://github.com/omise/omise-python) tutorial.

*If you run into any issues regarding this tool and the functionality it provides, consult the frequently asked questions in our [comprehensive support documents](https://www.omise.co/support).*
*If you can't find an answer there, post a question in our [forum](https://forum.omise.co/c/development) or feel free to [email our support team](mailto:support@omise.co).*

## Requirements

To follow along, you will need:

* An Omise account (and your `$OMISE_PUBLIC_KEY` and `$OMISE_SECRET_KEY`)
* A Python 3.7 environment (we are using [Pipenv](https://pipenv.readthedocs.io/en/latest/) here)

## Installation

The first step is to clone the repo:

```
git clone https://github.com/omise/omise-flask-example
```

Change to the `omise-flask-example` directory and install using [Pipenv](https://pipenv.readthedocs.io/en/latest/) (you will have to have already installed Pipenv itself).

```
cd omise-flask-example
pipenv install
```

## Configuration

Use the `env.example` template to create your `.env`.
Environment variables are a good way to prevent secret keys from leaking into your code (see [The Twelve-Factor App](https://12factor.net/)).
This file defines the environment variables that our app will need.

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
```

We need to replace the values of `OMISE_SECRET_KEY` and `OMISE_PUBLIC_KEY` with the actual keys for your account.
They can be found on your [Omise Dashboard](https://dashboard.omise.co).
After logging in, click "Keys" in the lower-left corner.
Copy and paste them into this file.

For `FLASK_SECRET_KEY`, create a random string of characters.
How to best do this is left as an [exercise for the reader](https://media.giphy.com/media/o0vwzuFwCGAFO/giphy.gif).

*The above currency and locale assume a test account registered in Thailand.*
*If you are using a test account registered in Japan, youshould also set `STORE_CURRENCY=JPY` and `STORE_LOCALE=ja_JP`.*
*For Singapore, you should set `STORE_CURRENCY=SGD` and `STORE_LOCALE=en_SG`.*

At this point, you should be able to run the app by typing the
following and hitting `ENTER`:

```
pipenv run flask run
```

The Flask app should be running at [http://localhost:5000](http://localhost:5000).
Go look at it, add some items to the cart, and hit checkout (you can use [these test credit card numbers](https://www.omise.co/api-testing).

![pipenv run flask run](https://omise-cdn.s3.amazonaws.com/assets/screenshots/omise-flask-example/pipenv-run-flask-run.gif)

## How Was This Made?

The source code should be fairly minimal and (hopefully) easy to understand.
For the rest of this `README.md`, let's walk through one way to integrate the Omise payment gateway as defined by this basic Flask app.
We will:

- Create an App Factory
- Define a Blueprint
- Prepare to Charge a Credit Card
- Handle Failure Conditions
- Successfully Charge That Credit Card

### Build Your Factory

At the root of your `omise-flask-example` directory should be `app.py`.
`app.py` sets up the configuration for this Flask app.
It defines the [application factory](http://flask.pocoo.org/docs/1.0/patterns/appfactories/) `create_app` which creates the Flask app.
This factory does the following:

1. Initializes our Flask `app`
1. Configures the app using the `Config` class (loaded from `config.py`)
1. Registers two blueprints (using the `register_blueprint` method) on the Flask `app
1. Returns the created `app`

```python
from flask import Flask, render_template, session
from config import Config
from store.store import store
from payment.checkout import checkout


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(store)
    app.register_blueprint(checkout)

    return app
```

Notice that there's not actually very much payment-related going on here.
The actual mechanics of charging a credit card are stored in the `checkout` blueprint we registered on the app above.
[Blueprints](http://flask.pocoo.org/docs/1.0/blueprints/) are Flask design pattern that helps manage modular Flask applications.
From the documentation:

> Flask uses a concept of blueprints for making application components and supporting common patterns within an application or across applications.
> Blueprints can greatly simplify how large applications work and provide a central means for Flask extensions to register operations on applications.
> A Blueprint object works similarly to a Flask application object, but it is not actually an application.
> Rather it is a blueprint of how to construct or extend an application.

In theory, you could extract this blueprint, add more routes, and include it in your own Omise-powered Flask app.

### Laying Out the Blueprint

On disk, the `checkout` blueprint and its template are stored in a
folder called `payment` which looks like this:

```
$ tree payment
payment
├── checkout.py
└── templates
    └── checkout.html
```

To create this blueprint, we make an instance of the `Blueprint` class and define a `template_folder` under the current directory.
After that, we add a route to the instance the same way we would with a normal Flask `app` instance using the [route decorator](http://flask.pocoo.org/docs/1.0/api/#flask.Flask.route): `@checkout.route("/checkout")`.

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
        currency=current_app.config.get("STORE_CURRENCY")
    )
```

Now when the user goes to the `/checkout` route, this blueprint will handle the rendering using the template `checkout.html` passing in values for `key`, `cart`, `Price`, and `currency`.
The template displays a very simple cart and the Omise-specific `<form>` code which powers our payment button:

```html
<form class="checkout-form" name="checkoutForm" method="POST" action="/charge">
  <script type="text/javascript" src="https://cdn.omise.co/omise.js"
          data-key="{{ key }}"
          data-amount="{{ cart.total() }}"
          data-currency="{{ currency }}">
  </script>
</form>
```

The payment form generation is handled by [Omise.js](https://github.com/omise/omise.js) which (at a minimum) accepts a `key` (your `OMISE_PUBLIC_KEY`), `amount`, and `currency`.

![Payment Pop Up](https://omise-cdn.s3.amazonaws.com/assets/screenshots/omise-flask-example/payment-pop-up.gif)

Once the user clicks on the button "Pay with Omise", the form sends a `POST` request to our local `/charge` endpoint providing the parameter `omiseToken`.

### Getting Ready to Charge

**We use the token to issue the charge rather than the actual credit card details.**
**Never have credit card details stored on or pass through your server.**

Using Omise, we avoid the risk of having to [collect card information](https://www.omise.co/collecting-card-information) directly.
We can retrieve token in Flask by calling `request.form.get("omiseToken")`.
So, for our `/charge` endpoint, we do the following:

1. Get the cart information (to determine the price)
1. Get the `omiseToken` we need to actually issue the charge
1. Configure the `omise` object which issues the charge
1. Create an `order_id`

We configure the `omise` object by providing the `OMISE_SECRET_KEY` and `OMISE_API_VERSION` we provided at the initial configuration of the app.
While the API version is not strictly necessary, it is good practice to set this explicitly to ensure consistency of behavior in the future (see our guidelines for [API versioning](https://www.omise.co/api-versioning)).
After this, we can then create a UUID `order_id`.
This is also not necessary, but willbe useful later as an identifier of the transaction.

```python
@checkout.route("/charge", methods=["POST"])
def charge():
    cart = Cart()
    token = request.form.get("omiseToken")
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")
    order_id = uuid.uuid4()
```

### Attempting the Charge

We are almost ready to issue the charge request, but we should keep in mind that there are two ways for a charge API request to go wrong.
In the first case, the request could return in an [error object](https://www.omise.co/api-errors) with an HTTP status code (e.g. `401 Authentication Failure`).
When using `omise-python`, this type of failure can be handled with a `try/except` block.
Another way the request could fail is if the charge API request returns a [charge object](https://www.omise.co/charges-api) with a non-`None` `failure_code`.
Let's handle the `try/except` case first and re-visit the `failure_code` scenario.

You can test out this behavior by using a set of pre-defined credit card numbers designated to cause a particular `failure_code`.
These numbers are listed here: https://www.omise.co/api-testing

#### Try/Except

To create a charge using `omise-python`, we call `omise.Charge.create` which accepts a `token`, `amount`, and `currency`.
The `amount` and `currency` are retrieved from the session cart and the configured `STORE_CURRENCY`, respectively.

Optionally, we are also passing a [custom metadata parameter](https://www.omise.co/store-your-data-on-omise-with-the-metadata-api).
This object can be any shape, and I am using it to log the app that made this charge ("Omise Flask"), the current cart contents, and the `order_id` I generated above.

```python
    try:
        charge = omise.Charge.create(
            amount=cart.total(),
            currency=current_app.config.get("STORE_CURRENCY"),
            card=token,
            metadata={
              "app": "Omise Flask Example",
              "cart": {
                "items": cart.items()
              },
              "order_id": str(order_id)
            },
        )
```

If the charge returns an error within our `try` clause, we flash a message, log the error, and return to the checkout page.
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

#### Handling the Failure Code

Even if the charge does not result in an exception, there may still be a failure to process the charge.
If there is such a charge failure, the `failure_code` attribute will be populated with one of `insufficient_fund`, `stolen_or_lost_card`, `failed_processing`, `payment_rejected`, `invalid_security_code`, `failed_fraud_check`, or `invalid_account_number` with an accompanying `failure_message` explaining the failure.
We can then handle such an issue with the same flash/log/redirect behavior I showed above.

```python
   # try:
   # ...
        if charge.failure_code is not None:
            flash(
                f"""An error occurred.  Please try again or use a different card.
            Here is the message returned from the server: "{charge.failure_message}" """
            )
            current_app.logger.warning(
                f"Omise Failure Message: {charge.failure_message} ({charge.failure_code})"
            )
            return redirect(url_for("checkout.check_out"))
  # except:
  # ...
  # except:
  # ...
```

#### Successfully Charging

Of course, we are really here to *handle payments like a boss*.
If no exception was raised and `charge.failure_code` is `None`, we have successfully charged the card!
In the case of success, we:

1. Let the user know the charge with successful providing their Order ID
1. Log the charge ID and our internal order ID
1. Empty the cart
1. Return to the index

```python
   # try:
   # ...
   #    if charge.failure_code is not None:
   #    ...
        else:
            flash(f"Card successfully charged!  Order ID: {order_id}")
            current_app.logger.info(f"Successful charge: {charge.id}.  Order ID: {order_id}")
            cart.empty()
            return redirect(url_for("store.index"))
  # except:
  # ...
  # except:
  # ...
```

### Viewing the Dashboard

Check [your dashboard](https://dashboard.omise.co) to see the charge and all its associated details.

![Dashboard Details](https://omise-cdn.s3.amazonaws.com/assets/screenshots/omise-flask-example/dashboard-details.png)

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

Use `autopep8` for formatting:

```
pipenv install --dev
pipenv run autopep8 --in-place --recursive .
```
