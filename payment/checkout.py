import uuid
from flask import (
    Markup,
    Blueprint,
    render_template,
    request,
    current_app,
    flash,
    redirect,
    url_for,
)
import omise
from store.cart import Cart, Price

checkout = Blueprint("checkout", __name__, template_folder="templates")


def processed(chrg, already_redirected=False):
    """
    Process charge.
    """

    cart = Cart()
    order_id = chrg._attributes["metadata"]["order_id"]

    charge_is_pending_econtext = (
        chrg.status == "pending"
        and chrg.source is not None
        and chrg.source.type == "econtext" is not None
    )
    charge_is_pending_billpayment = (
        chrg.status == "pending"
        and chrg.source is not None
        and chrg.source._attributes.get("references") is not None
    )
    charge_is_pending_redirect_flow_source = (
        chrg.status == "pending"
        and chrg.authorize_uri is not None
        and already_redirected is False
    )

    if chrg.status == "successful":
        cart.empty()
        flash(f"Order {order_id} successfully completed.")
        return render_template("complete.html", order_id=order_id)

    if charge_is_pending_econtext:
        cart.empty()
        msg = f"Visit <a href='{chrg.authorize_uri}'>link</a> to complete order {order_id}."
        flash(Markup(msg))
        return redirect(url_for("store.index"))

    if charge_is_pending_billpayment:
        cart.empty()
        flash(f"Visit Tesco Lotus to complete order {order_id}.")
        return render_template("barcode.html", charge=chrg)

    if charge_is_pending_redirect_flow_source:
        return redirect(chrg.authorize_uri)

    if chrg.status == "expired":
        flash("Charge expired for order {order_id}.")
        return redirect(url_for("checkout.check_out"))

    if chrg.status == "failed":
        flash(f"Error ('{chrg.failure_message}') while processing {order_id}")
        return redirect(url_for("checkout.check_out"))

    flash("Error while processing {order_id}")
    return redirect(url_for("checkout.check_out"))


@checkout.route("/orders/<order_id>/complete")
def order(order_id):
    """
    Charge completion return URL.
    """

    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")

    search = omise.Search.execute("charge", **{"query": order_id})
    chrg = search[0]
    return processed(chrg, already_redirected=True)


@checkout.route("/checkout")
def check_out():
    """
    Create checkout page
    """

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
    """
    Try to create charge.
    """

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

        chrg = omise.Charge.create(
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

        return processed(chrg)

    except omise.errors.BaseError as error:
        flash(f"An error occurred.  Please contact support.  Order ID: {order_id}")
        current_app.logger.error(f"OmiseError: {repr(error)}.")
        return redirect(url_for("checkout.check_out"))
