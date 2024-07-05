from django.shortcuts import render

# Create your views here.
def cart_page(request, *args, **kwargs):
    return render(request, "checkout/cart.html", {})


def checkout_page(request, *args, **kwargs):
    return render(request, "checkout/checkout.html", {})
