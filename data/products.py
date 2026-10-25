from typing import NamedTuple

class Product(NamedTuple):
    id: int  # in the detail page URL: /inventory-item.html?id=<id>
    name: str
    slug: str  # in the cart buttons' data-test: add-to-cart-<slug> / remove-<slug>
    price: str  # as the site shows it

BIKE_LIGHT = Product(0, "Sauce Labs Bike Light", "sauce-labs-bike-light", "$9.99")
BOLT_T_SHIRT = Product(1, "Sauce Labs Bolt T-Shirt", "sauce-labs-bolt-t-shirt", "$15.99")
ONESIE = Product(2, "Sauce Labs Onesie", "sauce-labs-onesie", "$7.99")
RED_T_SHIRT = Product(3, "Test.allTheThings() T-Shirt (Red)", "test.allthethings()-t-shirt-(red)", "$15.99")
BACKPACK = Product(4, "Sauce Labs Backpack", "sauce-labs-backpack", "$29.99")
FLEECE_JACKET = Product(5, "Sauce Labs Fleece Jacket", "sauce-labs-fleece-jacket", "$49.99")

# The 6 products in id order: the order of the spinner grid, the slider and its dots
PRODUCTS = [BIKE_LIGHT, BOLT_T_SHIRT, ONESIE, RED_T_SHIRT, BACKPACK, FLEECE_JACKET]
