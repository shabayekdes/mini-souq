from django.shortcuts import render, get_object_or_404
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

def shop(request):
    categories = Category.objects.order_by('order')[:5]
    category_id = request.GET.get('category_id')
    sort_by = request.GET.get('sort_by', 'price_asc')

    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products = selected_category.product_set.all()
    else:
        products = Product.objects.all()

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')

    return render(request, 'shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category if category_id else None,
        'sort_by': sort_by,
    })
