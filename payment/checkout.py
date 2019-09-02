from flask import (
    Markup,
    Blueprint,
    render_template,
    request,
    session,
    current_app,
    flash,
    redirect,
    url_for,
)
from itertools import accumulate
import omise
from store.cart import Cart, Price
import uuid
import time

checkout = Blueprint("checkout", __name__, template_folder="templates")


def process_failure(charge):
    flash(
        "An error occurred.  Please try again or use a different card or payment method.  "
        + f"Here is the message returned from the server: '{charge.failure_message}' "
    )
    current_app.logger.warning(
        f"Omise Failure Message: {charge.failure_message} ({charge.failure_code})"
    )


def process_success(cart, charge, order_id):
    cart.empty()
    flash(f"Card successfully charged!  Order ID: {order_id}")
    current_app.logger.info(f"Successful charge: {charge.id}.  Order ID: {order_id}")


@checkout.route("/orders/<id>/complete")
def order(id):
    cart = Cart()
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    charge = omise.Charge.retrieve(session["charge_id"])
    order_id = session["order_id"]

    if charge.failure_code is not None:
        process_failure(charge)
    else:
        process_success(cart, charge, order_id)

    return render_template("complete.html", id=id)


@checkout.route("/checkout")
def check_out():
    cart = Cart()
    return render_template(
        "checkout.html",
        key=current_app.config.get("OMISE_PUBLIC_KEY"),
        cart=cart,
        Price=Price,
        currency=current_app.config.get("STORE_CURRENCY"),
    )


@checkout.route("/charge", methods=["POST"])
def charge():
    cart = Cart()
    token = request.form.get("omiseToken")
    source = request.form.get("omiseSource")
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")
    order_id = uuid.uuid4()

    try:
        if token:
            nonce = {"card": token}
        elif source:
            nonce = {"source": source}

        charge = omise.Charge.create(
            amount=cart.total(),
            currency=current_app.config.get("STORE_CURRENCY"),
            metadata={
                "app": "Omise Flask",
                "cart": {"items": cart.items()},
                "order_id": str(order_id),
            },
            return_uri=f"http://localhost:5000/orders/{order_id}/complete",
            **nonce,
        )

        if charge.failure_code is not None:
            process_failure(charge)
            return redirect(url_for("checkout.check_out"))
        if charge.source is not None and charge.source.type == "econtext" is not None:
            cart.empty()

            flash(
                Markup(
                    f"Please visit <a href='{charge.authorize_uri}'>this link</a> to complete the charge."
                )
            )
            return redirect(url_for("store.index"))
        elif charge.authorize_uri is not None:
            session["charge_id"] = charge.id
            session["order_id"] = order_id

            return redirect(charge.authorize_uri)
        elif (
            charge.source is not None
            and charge.source._attributes.get("references") is not None
        ):
            cart.empty()

            flash(f"Use this barcode to pay at Tesco Lotus.")
            return render_template(
                "barcode.html",
                charge=charge,
                ref=charge.source._attributes.get("references"),
            )
        else:
            process_success(charge, order_id)
            return redirect(url_for("store.index"))

    except omise.errors.BaseError as e:
        flash("""An error occurred.  Please contact support.  Order ID: {order_id} """)
        current_app.logger.error(
            f"""OmiseError: {repr(e)}.  See https://www.omise.co/api-errors"""
        )
        return redirect(url_for("checkout.check_out"))
    except Exception as e:
        flash("""An error occurred.  Please contact support.  Order ID: {order_id}""")
        current_app.logger.error(repr(e))
        return redirect(url_for("checkout.check_out"))
