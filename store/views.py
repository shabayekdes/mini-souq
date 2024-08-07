from django.shortcuts import render, get_object_or_404
from product.models import Brand, Category, Product

# Create your views here.
def home(request):
    products = Product.objects.all()
    categories = Category.objects.order_by('order')[:5]
    first_category = Category.objects.first()
    brands = Brand.objects.all()

    if first_category:
        category_products = first_category.product_set.all()
    else:
        category_products = []

    return render(request, 'home.html', {
        'products': products, 
        'brands': brands,
        'categories': categories, 
        'first_category': first_category, 
        'category_products': category_products
        })

def shop(request):
    categories = Category.objects.order_by('order')[:5]
    brands = Brand.objects.all()
    
    category_id = request.GET.get('category_id')
    brand_id = request.GET.get('brand_id')
    sort_by = request.GET.get('sort_by', 'price_asc')

    products = Product.objects.all()

    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=selected_category)
    else:
        selected_category = None

    if brand_id:
        selected_brand = get_object_or_404(Brand, id=brand_id)
        products = products.filter(brand=selected_brand)
    else:
        selected_brand = None

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')

    return render(request, 'shop.html', {
        'products': products,
        'brands': brands,
        'categories': categories,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'sort_by': sort_by,
    })
