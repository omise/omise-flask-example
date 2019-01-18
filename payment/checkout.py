from flask import (
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


@checkout.route("/charge", methods=["POST"])
def charge():
    cart = Cart()
    token = request.form.get("omiseToken")
    omise.api_secret = current_app.config.get("OMISE_SECRET_KEY")
    omise.api_version = current_app.config.get("OMISE_API_VERSION")
    order_id = uuid.uuid4()
    try:
        charge = omise.Charge.create(
            amount=cart.total(),
            currency=current_app.config.get("STORE_CURRENCY"),
            card=token,
            metadata={"app": "Omise Flask", "cart": {
                "items": cart.items()}, "order_id": str(order_id)},
        )

        if charge.failure_code is not None:
            flash(
                f"""An error occurred.  Please try again or use a different card.
            Here is the message returned from the server: "{charge.failure_message}" """
            )
            current_app.logger.warning(
                f"Omise Failure Message: {charge.failure_message} ({charge.failure_code})"
            )
            return redirect(url_for("checkout.check_out"))
        else:
            flash(f"Card successfully charged!  Order ID: {order_id}")
            cart.empty()
            current_app.logger.info(
                f"Successful charge: {charge.id}.  Order ID: {order_id}")
            return redirect(url_for("store.index"))
    except omise.errors.BaseError as e:
        flash("""An error occurred.  Please contact support.""")
        current_app.logger.error(
            f"""OmiseError: {repr(e)}.  See https://www.omise.co/api-errors""")
        return redirect(url_for("checkout.check_out"))
    except Exception as e:
        flash("""An error occurred.  Please contact support.""")
        current_app.logger.error(repr(e))
        return redirect(url_for("checkout.check_out"))
