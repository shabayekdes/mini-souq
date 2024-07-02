from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Product

# Create your views here.
def product_details(request, id=None, *args, **kwargs):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product/details.html', {"product": product})
