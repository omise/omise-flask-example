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


def processed(charge, cart, order_id, already_redirected=False):
    charge_is_pending_econtext = (
        charge.status == "pending"
        and charge.source is not None
        and charge.source.type == "econtext" is not None
    )
    charge_is_pending_barcode = (
        charge.status == "pending"
        and charge.source is not None
        and charge.source._attributes.get("references") is not None
    )
    charge_is_pending_redirect_flow_source = (
        charge.status == "pending"
        and charge.authorize_uri is not None
        and already_redirected is False
    )

    if charge.status == "successful":
        cart.empty()
        flash(f"Payment method successfully charged.  Order ID: {order_id}")
        return render_template("complete.html", order_id=order_id)
    elif charge_is_pending_econtext:
        cart.empty()
        flash(
            Markup(
                f"Please visit <a href='{charge.authorize_uri}'>this link</a> to complete the charge."
            )
        )
        return redirect(url_for("store.index"))
    elif charge_is_pending_barcode:
        cart.empty()
        flash(f"Use this barcode to pay at Tesco Lotus. Order ID: {order_id}")
        return render_template(
            "barcode.html",
            charge=charge,
            ref=charge.source._attributes.get("references"),
        )
    elif charge_is_pending_redirect_flow_source:
        session["charge_id"] = charge.id
        session["order_id"] = order_id

        return redirect(charge.authorize_uri)
    elif charge.status == "expired":
        flash("Charge expired.")
        return redirect(url_for("checkout.check_out"))
    elif charge.status == "failed":
        flash(
            "An error occurred.  Please try again or use a different card or payment method.  "
            + f"Here is the message returned from the server: '{charge.failure_message}' "
        )
        return redirect(url_for("checkout.check_out"))
    else:
        flash("An unknown error occurred")
        return redirect(url_for("checkout.check_out"))


@checkout.route("/orders/<order_id>/complete")
def order(order_id):
    cart = Cart()
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")
    charge = omise.Charge.retrieve(session["charge_id"])

    return processed(charge, cart, order_id, already_redirected=True)


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
            return_uri=f"https://omise-flask-example.herokuapp.com/orders/{order_id}/complete",
            **nonce,
        )

        return processed(charge, cart, order_id)

    except omise.errors.BaseError as e:
        flash(f"An error occurred.  Please contact support.  Order ID: {order_id}")
        current_app.logger.error(
            f"OmiseError: {repr(e)}.  See https://www.omise.co/api-errors"
        )
        return redirect(url_for("checkout.check_out"))
    except Exception as e:
        flash(f"An error occurred.  Please contact support.  Order ID: {order_id}")
        current_app.logger.error(repr(e))
        return redirect(url_for("checkout.check_out"))
