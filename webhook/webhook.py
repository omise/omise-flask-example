from flask import Blueprint, request, session, current_app, flash, redirect, url_for


webhook = Blueprint("webhook", __name__)


@webhook.route("/webhook", methods=["POST"])
def order():
    event = request.json
    current_app.logger.info(f"Event: {event['key']}")
    if event["data"]["object"] == "charge":
        charge_status = event["data"]["status"]
        current_app.logger.info(f"Event: {charge_status}")
    return redirect("/")
