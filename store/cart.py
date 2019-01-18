from flask import session, current_app
from functools import reduce
from collections import Counter
import operator
from money.money import Money
from money.currency import Currency


class Price:
    prices = {"nuts.jpg": 3000, "bolts.jpg": 2000}

    def __init__(self, **kwargs):
        if "item" in kwargs:
            self.amount = self.prices[kwargs["item"]]
        elif "amount" in kwargs:
            self.amount = kwargs["amount"]
        else:
            self.amount = 0

    def __str__(self):
        currency = current_app.config.get("STORE_CURRENCY")
        m = Money.from_sub_units(self.amount, Currency[currency.upper()])
        locale = current_app.config.get("STORE_LOCALE")
        return str(m.format(locale))


class Cart:
    def __init__(self):
        if "cart" not in session:
            session["cart"] = []

    def empty(self):
        session["cart"] = []

    def items(self):
        client_cart = session["cart"]
        return [
            (item, units, Price(item=item).amount, Price(item=item).amount * units)
            for (item, units) in Counter(client_cart).items()
        ]

    def total(self):
        return reduce(operator.add, [item[3] for item in self.items()], 0)
