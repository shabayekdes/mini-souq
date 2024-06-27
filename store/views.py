from django.shortcuts import render

from product.models import Category, Product

# Create your views here.
def home(request):
    products = Product.objects.all()
    categories = Category.objects.order_by('order')[:5]
    first_category = Category.objects.first()

    if first_category:
        category_products = first_category.product_set.all()
    else:
        category_products = []

    return render(request, 'home.html', {'products': products, 'categories': categories, 'first_category': first_category, 'category_products': category_products})
