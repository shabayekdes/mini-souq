from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CheckoutForm
from .models import Cart, CartItem, OrderItem
from product.models import Product
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'checkout/cart_detail.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart_detail')

@login_required
def checkout_page(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return redirect('shop')

    if not cart.cartitem_set.exists():
        return redirect('shop')

    cart_items = CartItem.objects.filter(cart=cart)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = sum(item.item_price() for item in cart_items)
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.item_price()
                )
            cart_items.delete()
            return redirect('order_success')
    else:
        form = CheckoutForm()

    return render(request, 'checkout/checkout.html', {'form': form, 'cart_items': cart_items})

@login_required
def order_success(request):
    return render(request, 'checkout/order_success.html')
