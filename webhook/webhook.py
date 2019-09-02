from flask import Blueprint, request, session, current_app, flash, redirect, url_for

import omise


webhook = Blueprint("webhook", __name__)


@webhook.route("/webhook", methods=["POST"])
def order():
    event = request.form.get("event")
    current_app.logger.info(request)

    return redirect("/")
