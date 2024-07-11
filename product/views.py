from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Product
from django.db.models import Q

# Create your views here.
def product_details(request, id=None, *args, **kwargs):
    product = get_object_or_404(Product, id=id)
    related_products = Product.objects.filter(
        Q(category=product.category) | Q(brand=product.brand)
    ).exclude(id=id)[:5] 

    return render(request, 'product/details.html', {
        "product": product,
        "related_products": related_products
        })
