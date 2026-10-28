from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from product.models import Product

from .forms import AddToCartForm, CheckoutForm
from .models import MAX_QUANTITY_PER_ITEM, Cart, CartItem, OrderItem


def _cart_items(cart):
    return CartItem.objects.filter(cart=cart).select_related('product')


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please choose a quantity between 1 and %d.' % MAX_QUANTITY_PER_ITEM)
        return redirect(product.get_absolute_url())

    quantity = form.cleaned_data['quantity']
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity = min(cart_item.quantity + quantity, MAX_QUANTITY_PER_ITEM)
        cart_item.save(update_fields=['quantity'])
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = list(_cart_items(cart)) if cart else []
    total_price = sum(item.item_price() for item in cart_items)
    return render(request, 'checkout/cart_detail.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
@require_POST
def remove_from_cart(request, item_id):
    # Scope the lookup to the current user's cart so IDs can't be guessed.
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')

@login_required
def checkout_page(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart is None or not cart.cartitem_set.exists():
        return redirect('shop')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Lock the cart so concurrent/double submissions are serialised;
                # the second request then sees an empty cart.
                Cart.objects.select_for_update().get(pk=cart.pk)
                cart_items = list(_cart_items(cart))
                if not cart_items:
                    return redirect('cart_detail')

                order = form.save(commit=False)
                order.user = request.user
                order.total_amount = sum(item.item_price() for item in cart_items)
                order.save()
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.current_price,
                    )
                    for item in cart_items
                ])
                CartItem.objects.filter(cart=cart).delete()
            return redirect('order_success')
    else:
        form = CheckoutForm()

    cart_items = list(_cart_items(cart))
    total_price = sum(item.item_price() for item in cart_items)
    return render(request, 'checkout/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required
def order_success(request):
    return render(request, 'checkout/order_success.html')
