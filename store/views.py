from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from product.models import Brand, Category, Product

PRODUCTS_PER_PAGE = 24
SORT_OPTIONS = {
    'price_asc': 'price',
    'price_desc': '-price',
}


def _get_filter_object(model, raw_id):
    """Resolve an optional ?<model>_id= query parameter, 404 on bad input."""
    if not raw_id:
        return None
    try:
        pk = int(raw_id)
    except ValueError:
        raise Http404(f'Invalid {model._meta.verbose_name} id')
    return get_object_or_404(model, pk=pk)


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

    selected_category = _get_filter_object(Category, request.GET.get('category_id'))
    selected_brand = _get_filter_object(Brand, request.GET.get('brand_id'))
    sort_by = request.GET.get('sort_by')
    if sort_by not in SORT_OPTIONS:
        sort_by = 'price_asc'

    products = Product.objects.all()
    if selected_category:
        products = products.filter(category=selected_category)
    if selected_brand:
        products = products.filter(brand=selected_brand)
    # Secondary ordering by id keeps pagination stable for equal prices.
    products = products.order_by(SORT_OPTIONS[sort_by], 'id')

    page_obj = Paginator(products, PRODUCTS_PER_PAGE).get_page(request.GET.get('page'))

    return render(request, 'shop.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'brands': brands,
        'categories': categories,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'sort_by': sort_by,
    })
