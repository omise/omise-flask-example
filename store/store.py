from flask import Blueprint, render_template, request, session, redirect, url_for
import omise
import os
from store.cart import Price

store = Blueprint(
    "store", __name__, static_folder="assets", template_folder="templates"
)


@store.route("/")
def index():
    assets = os.listdir(os.path.join(store.static_folder))
    images = [a for a in assets if a.endswith('.jpg')]
    return render_template("store.html", images=images, Price=Price)


@store.route("/add", methods=["POST"])
def add():
    item = request.form.get("item")
    if "cart" in session:
        session["cart"] = session["cart"] + [item]
    else:
        session["cart"] = [item]
    return redirect(url_for("store.index"))
